#!/usr/local/bin/python3
#
# CONFIGURATION IS MINIMAL BY DESIGN...
# INPUT YOUR KUCOIN FUTURES API KEYS IN THE EMPTY QUOTES BELOW TO LINK YOUR ACCT
API_KEY = ''
API_SECRET = ''
API_PASSWD = ''

# THESE ARE RATIOS, NOT PERCENTS. [ 1 = 100% ][ 0.05 = 5% ][ 0.1 = 10% ] ETC...
stopLoss = -0.05
takeProfit = 1

# HOW MANY LOTS TO BUY OR SELL AT A TIME PER INTERVAL/SIGNAL - BOT WILL BUY SEVERAL TIMES IF THERE ARE MULTIPLE SIGNALS
lotsPerTrade = 1

### END OF CONFIG ###

try:
    from ta import trend, momentum, volatility, volume
    from pandas import DataFrame as dataframe
    from ccxt import kucoinfutures as kucoin
    import time
    import datetime
except Exception:
    import subprocess
    import sys
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "ccxt", "pandas", "numpy", "ta", "datetime", "-U"])
    from ta import trend, momentum, volatility, volume
    from pandas import DataFrame as dataframe
    from ccxt import kucoinfutures as kucoin
    import time
    import datetime

exchange = kucoin({
    'adjustForTimeDifference': True,
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSWD
})


def getData(coin, tf):
    data = exchange.fetch_ohlcv(coin, tf, limit=500)
    df = {}
    for i, col in enumerate(['date', 'open', 'high', 'low', 'close',
                             'volume']):
        df[col] = []
        for row in data:
            if col == 'date':
                df[col].append(datetime.datetime.fromtimestamp(row[i] / 1000))
            else:
                df[col].append(row[i])
        DF = dataframe(df)
    return DF


def rsi(close, w):
    return momentum.rsi(close, w)


def sma(close, w):
    return trend.sma_indicator(close, w)


def vwap(h, l, c, v, w):
    return volume.volume_weighted_average_price(h, l, c, v, w)


class kc:
    def h(h, l, c):
        return volatility.keltner_channel_hband(h, l, c, 10)

    def l(h, l, c):
        return volatility.keltner_channel_lband(h, l, c, 10)


class order:
    def buy():
        if side == 'short':
            price = (exchange.fetch_order_book(coin)[
                     'bids'][0][0] + exchange.fetch_order_book()['asks'][0][0])/2
            qty = contracts
            params = {'reduceOnly': True, 'closeOrder': True}
        else:
            price = exchange.fetch_order_book(coin)['bids'][0][0]
            qty = lotsPerTrade
            params = {'leverage': leverage}
        print(
            f'Buy order placed... for {coin}, {qty} contracts at {100*pnl}%')
        try:
            exchange.create_limit_buy_order(coin, qty, price, params=params)
        except Exception as e:
            print(e)
        return

    def sell():
        price = (exchange.fetch_order_book(coin)[
                 'bids'][0][0] + exchange.fetch_order_book(coin)['asks'][0][0])/2
        if side == 'long':
            qty = contracts
            params = {'reduceOnly': True, 'closeOrder': True}
        else:
            qty = lotsPerTrade
            params = {'leverage': leverage}
        print(
            f'Sell order placed... for {coin}')
        try:
            exchange.create_limit_sell_order(coin, qty, price, params=params)
        except Exception as e:
            print(e)
        return

    def stopLimit():
        if pnl > takeProfit or pnl < stopLoss:
            price = (exchange.fetch_order_book()[
                     'bids'][0][0] + exchange.fetch_order_book(coin)['asks'][0][0])/2
            qty = contracts
            params = {'reduceOnly': True, 'closeOrder': True}
            print(f'Closed {coin}, {contracts} contracts at {pnl*100}%')
            fac = 'buy' if side == 'short' else 'sell' if side == 'long' else None
            try:
                exchange.create_limit_order(
                    coin, fac, qty, price, params=params)
            except Exception as e:
                print(e)
        return

################################################################################
def bot():
    h = getData(coin, tf)['high']
    l = getData(coin, tf)['low']
    c = getData(coin, tf)['close']
    o = getData(coin, tf)['open']
    v = getData(coin, tf)['volume']
    Close = c.iloc[-1]
    High = h.iloc[-1]
    Low = l.iloc[-1]
    Open = o.iloc[-1]
    lowerBand = kc.l(h, l, c).iloc[-1]
    upperBand = kc.h(h, l, c).iloc[-1]
    vw = vwap(h, l, c, v, 200).iloc[-1]
    ma200 = sma(c, 200).iloc[-1]
    ma20 = sma(c, 20).iloc[-1]
    rsi14 = rsi(c, 14).iloc[-1]
    print(f'{tf} {coin} {side} ... CONTRACTS: {contracts} ... TOTAL: {equity}')
    
    if High > upperBand and rsi14 > 70 and Open > (Close and ma200 and vw):
        order.sell()

    if High > upperBand and rsi14 < 70 and Close > (Open and ma200 and vw):
        order.buy()

    if Low < lowerBand and rsi14 > 30 and  Close < (Open and ma200 and vw):
        order.sell()

    if Low < lowerBand and rsi14 < 30 and Open < (Open and ma200 and vw):
        order.buy()

    order.sell() if side == 'long' and Low < ma20 else order.buy() if side == 'short' and High > ma20 else order.stopLimit()

 ###############################################################################


print('\n'*100, 'TRADE AT YOUR OWN RISK. CRYPTOCURRENCY FUTURES TRADES ARE NOT FDIC INSURED. RESULTS ARE NOT GUARANTEED. POSITIONS MAY LOSE VALUE SUDDENLY AND WITHOUT WARNING. POSITINOS ARE SUBJECT TO LIQUIDATION. THERE ARE RISKS ASSOCIATED WITH ALL FORMS OF TRADING. IF YOU DON\'T UNDERSTAND THAT, THEN YOU SHOULD NOT BE TRADING IN THE FIRST PLACE. THIS SOFTWARE IS DEVELOPED FOR MY OWN USE, AND IS NOT TO BE INTERPRETED AS FINANCIAL ADVICE.')
time.sleep(2)
print('\n'*100, '...AND MOST OF ALL HAVE FUN!!\n')
time.sleep(1)
print('\n'*100)
positions = exchange.fetch_positions()
markets = exchange.load_markets()
balance = exchange.fetch_balance({'currency': 'USDT'})['free']['USDT']
equity = exchange.fetch_balance()['info']['data']['accountEquity']
while True:
    movers = {}
    tfs = ['1m', '5m', '15m']
    for tf in tfs:
        leverage = 20 if tf == '1m' else 15 if tf == '5m' else 10
        for coin in exchange.load_markets():
            if '/USDT:USDT' not in coin:
                pass
            movers[coin] = abs(coin['priceChgPct'])
            if coin not in dict(enumerate(positions)).values():
                contracts = 0
                side = 'none'
                pnl = 0
                bot()
            else:
                pos = {}
                for i, v in enumerate(positions):
                    side = v['side']
                    contracts = v['contracts']
                    pnl = v['percentage']
                    bot()
