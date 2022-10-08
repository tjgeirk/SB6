#!/usr/local/bin/python3
#
# CONFIGURATION IS MINIMAL BY DESIGN...
# INPUT YOUR KUCOIN FUTURES API KEYS IN THE EMPTY QUOTES BELOW TO LINK YOUR ACCT
API_KEY = ''
API_SECRET = ''
API_PASSWD = ''

# LISTS OF COINS AND TIMEFRAMES FOR MULTI-COIN SCANNING.
# TO USE A STATIC TF OR COIN (OR BOTH), LEAVE ONLY ONE VALUE IN EACH LIST.
coins = ['BTC', 'ETH', 'LUNA', 'LUNC', 'XLM']
tfs = ['1m', '5m', '15m', '30m', '1h']

# THESE ARE RATIOS, NOT PERCENTS. [ 1 = 100% ][ 0.05 = 5% ][ 0.1 = 10% ] ETC...
stopLoss = -0.05
takeProfit = 0.1

# REFER TO EXCHANGE FOR PRICES PER LOT. BOT USES D.C.A. ENTRY, SO THIS IS NOT THE TOTAL POSITION SIZE, ONLY THE NUMBER OF LOTS TO BUY/SHORT *AT A TIME*
# APPLIES ONLY TO OPENING POSITIONS. CLOSING IS ALWAYS THE FULL POSITION SIZE.
lotsPerTrade = 1

### END ###

tc = dict(enumerate(tfs, 0))
ttc = int(len(tfs) - 1)
tf = tc[0]
cc = dict(enumerate(coins, 0))
ccc = int(len(coins) - 1)
coinName = cc[0]
coin = str(f'{coinName}/USDT:USDT')
lock = False

try:
    from ta import trend, momentum, volatility
    from pandas import DataFrame as dataframe
    from ccxt import kucoinfutures as kucoin
    import time
    import datetime
except Exception:
    import subprocess
    import sys
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "ccxt", "pandas", "numpy", "ta", "datetime", "-U"])
    from ta import trend, momentum, volatility
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
positions = exchange.fetch_positions()


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


class kc:
    def h(h, l, c):
        return volatility.keltner_channel_hband(h, l, c, 10)

    def l(h, l, c):
        return volatility.keltner_channel_lband(h, l, c, 10)


class order:
    def buy():
        if side == 'short':
            price = sma(c, 20).iloc[-1]
            qty = contracts
            params = {'reduceOnly': True, 'closeOrder': True}
        else:
            price = lowerBand
            qty = lotsPerTrade
            params = {'leverage': leverage}
        print(
            f'Buy order placed... for {coin}, {contracts} contracts at {pnl}%')
        return exchange.create_limit_buy_order(coin, qty, price, params=params)

    def sell():
        if side == 'long':
            price = sma(c, 20).iloc[-1]
            qty = contracts
            params = {'reduceOnly': True, 'closeOrder': True}
        else:
            price = upperBand
            qty = lotsPerTrade
            params = {'leverage': leverage}
        print(
            f'Sell order placed... for {coin}, {contracts} contracts at {pnl}%')
        return exchange.create_limit_sell_order(coin, qty, price, params=params)


def drop():
    if side == 'long' and pnl < stopLoss:
        return exchange.create_market_sell_order(coin, contracts, {
            'reduceOnly': True, 'closeOrder': True})
    elif side == 'short' and pnl < stopLoss:
        return exchange.create_market_buy_order(coin, contracts, {
            'reduceOnly': True, 'closeOrder': True})


print('\n'*100, 'TRADE AT YOUR OWN RISK. CRYPTOCURRENCY FUTURES TRADES ARE NOT FDIC INSURED. RESULTS ARE NOT GUARANTEED. POSITIONS MAY LOSE VALUE SUDDENLY AND WITHOUT WARNING. POSITINOS ARE SUBJECT TO LIQUIDATION. THERE ARE RISKS ASSOCIATED WITH ALL FORMS OF TRADING. IF YOU DON\'T UNDERSTAND THAT, THEN YOU SHOULD NOT BE TRADING IN THE FIRST PLACE. THIS SOFTWARE IS DEVELOPED FOR MY OWN USE, AND IS NOT TO BE INTERPRETED AS FINANCIAL ADVICE.')
time.sleep(2)
print('\n'*100, '...AND MOST OF ALL HAVE FUN!!\n')
time.sleep(1)
print('\n'*100)
lock = False
while True:
    try:
        exchange.load_markets()
        balance = round(
            exchange.fetch_balance()['info']['data']['accountEquity'], 2)
        try:
            exchange.cancel_all_orders()if len(
                exchange.fetch_open_orders()) > 3 else time.sleep(1)
            coin = positions[0]['symbol']
            side = positions[0]['side']
            contracts = positions[0]['contracts']
            pnl = positions[0]['percentage']
        except Exception:
            exchange.cancel_all_orders()if len(
                exchange.fetch_open_orders()) > 0 else time.sleep(1)
            if lock == False:
                side = 'none'
                pnl = 0
                contracts = 0
                ccc = ccc + 1
                if ccc >= len(coins):
                    ccc = 0
                    ttc = ttc + 1
                    if ttc >= len(tfs):
                        ttc = 0
                    tf = tc[ttc]
                coinName = cc[ccc]
                coin = str(f'{coinName}/USDT:USDT')
        if tf == '1m':
            leverage = 10
        elif tf == '5m':
            leverage = 5
        else:
            leverage = 2
        print(
            f'{tf} {coin} {side} ... CONTRACTS: {contracts} ... PNL: {round(100*pnl,2)}% ... TOTAL: {balance}')
        h = getData(coin, tf)['high']
        l = getData(coin, tf)['low']
        c = getData(coin, tf)['close']
        lowerBand = kc.l(h, l, c)
        upperBand = kc.h(h, l, c)

        if upperBand.iloc[-2] < c.iloc[-2] < sma(c, 200).iloc[-2] and c.iloc[-1] < upperBand.iloc[-1] < sma(c, 200).iloc[-2]:
            lock = True if side != 'long' else False
            order.sell()
        if lowerBand.iloc[-2] > c.iloc[-1] > sma(c, 200).iloc[-2] and c.iloc[-1] > lowerBand.iloc[-1] > sma(c, 200).iloc[-1]:
            lock = True if side != 'short' else False
            order.buy()

        order.sell() if side == 'long' and pnl < stopLoss or pnl > takeProfit else order.buy(
        ) if side == 'short' and pnl < stopLoss or pnl > takeProfit else time.sleep(1)
    except Exception as e:
        exchange.cancel_all_orders()
        print(e)
        time.sleep(3)
