API_KEY = ''
API_SECRET = ''
API_PASSWD = ''

coins = ['ETH', 'XRP', 'ETC', 'BTC', 'LUNC', 'LUNA']
stopLoss = -0.03
takeProfit = 0.1

lotsPerTrade = 1
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


class bb:
    def h(close, window, deviations):
        return volatility.bollinger_hband(close, window, deviations)

    def l(close, window, deviations):
        return volatility.bollinger_lband(close, window, deviations)

#############################################################


class order:
    def buy(coin, contracts, side):
        ask = exchange.fetch_order_book(coin)['bids'][0][0]
        if side == 'short':
            amount = contracts
            params = {'reduceOnly': True, 'closeOrder': True}
        if side != 'short':
            amount = lotsPerTrade
            params = {'leverage': leverage}

        return exchange.create_limit_buy_order(coin, amount, ask, params=params)

    def sell(coin, contracts, side):
        bid = exchange.fetch_order_book(coin)['asks'][0][0]
        if side == 'long':
            amount = contracts
            params = {'reduceOnly': True, 'closeOrder': True}
        if side != 'long':
            amount = lotsPerTrade
            params = {'leverage': leverage}
        return exchange.create_limit_sell_order(coin, amount, bid, params=params)


def bot(coin, contracts, side, pnl):
    h = getData(coin, tf)['high']
    l = getData(coin, tf)['low']
    c = getData(coin, tf)['close']
    o = getData(coin, tf)['open']
    v = getData(coin, tf)['volume']

    Close = c.iloc[-1]
    High = h.iloc[-1]
    Low = l.iloc[-1]
    Open = o.iloc[-1]

    hammer = (Close < Open and abs(Close - Low) > abs(High - Open)) or (
        Close > Open and abs(Open - Low) > abs(High - Close))

    invHammer = (Close < Open and abs(Close - Low) < abs(High - Open)) or (
        Close > Open and abs(Open - Low) < abs(High - Close))

    lower20 = bb.l(c, 20, 2).iloc[-1]
    upper20 = bb.h(c, 20, 2).iloc[-1]
    lower5 = bb.l(c, 5, 2).iloc[-1]
    upper5 = bb.h(c, 5, 2).iloc[-1]
    sma200 = sma(c, 200).iloc[-1]

    try:
        if Low < lower5 and (Close > sma200 or side == 'short'):
            order.buy(coin, contracts, side)

        if High > upper5 and (Close < sma200 or side == 'long'):
            order.sell(coin, contracts, side)

        if side == 'long' and High > upper20 or upper5:
            order.sell(coin, contracts, side)

        if High > upper20 and invHammer and (Close < sma200 or side == 'long'):
            order.sell(coin, contracts, side)

        if Low < lower20 and hammer and (Close > sma200 or side == 'short'):
            order.buy(coin, contracts, side)

    except Exception as e:
        print(e)


print('\n'*100, 'TRADE AT YOUR OWN RISK. CRYPTOCURRENCY FUTURES TRADES ARE NOT FDIC INSURED. RESULTS ARE NOT GUARANTEED. POSITIONS MAY LOSE VALUE SUDDENLY AND WITHOUT WARNING. POSITINOS ARE SUBJECT TO LIQUIDATION. THERE ARE RISKS ASSOCIATED WITH ALL FORMS OF TRADING. IF YOU DON\'T UNDERSTAND THAT, THEN YOU SHOULD NOT BE TRADING IN THE FIRST PLACE. THIS SOFTWARE IS DEVELOPED FOR MY OWN USE, AND IS NOT TO BE INTERPRETED AS FINANCIAL ADVICE.')
time.sleep(2)
print('\n'*100, '...AND MOST OF ALL HAVE FUN!!\n')
time.sleep(1)
print('\n'*100)
while True:
    positions = exchange.fetch_positions()
    markets = exchange.load_markets()
    balance = exchange.fetch_balance({'currency': 'USDT'})['free']['USDT']
    equity = exchange.fetch_balance()['info']['data']['accountEquity']
    tfs = ['1m', '5m', '15m']
    for tf in tfs:
        leverage = 20 if tf == '1m' else 15 if tf == '5m' else 10
        for symbol in coins:
            try:
                for i,v in enumerate(positions):
                    coin = v['symbol']
                    pnl = v['percentage']
                    contracts = v['contracts']
                    side = v['side']
                    if pnl < stopLoss or pnl > takeProfit:
                        if side == 'long':
                            order.sell(coin, contracts)
                        elif side == 'short':
                            order.buy(coin, contracts)
                    print(f'{tf} {coin} {side} {contracts} {pnl}% TOTAL: {equity}')
                    bot(coin, contracts, side, pnl)
            except Exception as e:
                coin = str(symbol+'/USDT:USDT')
                pnl = 0
                contracts = 0
                side = 'none'
                print(f'{tf} {coin} {side} {contracts} {pnl}% TOTAL: {equity}')
                bot(coin, contracts, side, pnl)

        exchange.cancel_all_orders() if len(exchange.fetch_open_orders()) > 10 else 0
