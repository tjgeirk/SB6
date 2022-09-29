from ta import trend, momentum, volatility
from pandas import DataFrame as dataframe
import ccxt
import time
import datetime

API_KEY = ''
API_SECRET = ''
API_PASSWD = ''

coins = ['APE', 'ETH', 'LUNA', 'LUNC']
tfs = ['1m', '5m', '15m', '30m', '1h']
lotsPerTrade = 1
leverage = 10
stopLoss = -5
takeProfit = 10

## end of config ##

tc = dict(enumerate(tfs, 0))
ttc = int(len(tfs)-1)
tf = tc[0]
cc = dict(enumerate(coins, 0))
ccc = int(len(coins)-1)
coinName = cc[0]
side = 'none'
stopLoss = int(-abs(stopLoss))
takeprofit = int(abs(takeProfit))
exchange = ccxt.kucoinfutures({
    'adjustForTimeDifference': True,
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSWD
})


def getData(coin, tf):
    data = exchange.fetch_ohlcv(coin, timeframe=tf, limit=500)
    df = {}
    for i, col in enumerate(['date', 'open', 'high', 'low', 'close', 'volume']):
        df[col] = []
        for row in data:
            if col == 'date':
                df[col].append(datetime.datetime.fromtimestamp(row[i]/1000))
            else:
                df[col].append(row[i])
        DF = dataframe(df)
    return DF


def hashi(df):
    hashi_df = dataframe(index=df.index.values, columns=[
        'open', 'high', 'low', 'close'])
    hashi_df['date'] = df['date']
    hashi_df['close'] = (
        df['open'] + df['high'] + df['low'] + df['close']) / 4
    for i in range(len(df)):
        if i == 0:
            hashi_df.iat[0, 0] = df['open'].iloc[0]
        else:
            hashi_df.iat[i, 0] = (
                hashi_df.iat[i-1, 0] + hashi_df.iat[i-1, 3]) / 2
    hashi_df['high'] = hashi_df.loc[:, [
        'open', 'close']].join(df['high']).max(axis=1)
    hashi_df['low'] = hashi_df.loc[:, [
        'open', 'close']].join(df['low']).min(axis=1)
    return hashi_df


def rsi(c, w):
    rsi = momentum.rsi(c, w).iloc[-1]
    return rsi


def sma(c, w):
    sma = trend.sma_indicator(c, w).iloc[-1]
    return sma


class bb:
    def h(c):
        h = volatility.bollinger_hband_indicator(c).iloc[-1]
        return h

    def l(c):
        l = volatility.bollinger_lband_indicator(c).iloc[-1]
        return l


class order:

    def buy():
        bid = exchange.fetch_order_book(coin)['bids'][0][0]

        if side == 'short':
            qty = contracts
            params = {'reduceOnly': True, 'closeOrder': True}

        else:
            qty = lotsPerTrade
            params = {'leverage': leverage}

        placeOrder = exchange.create_limit_buy_order(
            coin, qty, bid, params=params)
        return placeOrder

    def sell():
        ask = exchange.fetch_order_book(coin)['asks'][0][0]

        if side == 'long':
            qty = contracts
            params = {'reduceOnly': True, 'closeOrder': True}

        else:
            qty = lotsPerTrade
            params = {'leverage': leverage}

        placeOrder = exchange.create_limit_sell_order(
            coin, qty, ask, params=params)
        return placeOrder


while True:
    exchange.load_markets()
    balance = round(
        exchange.fetch_balance()['info']['data']['accountEquity'], 2)
    positions = exchange.fetch_positions()

    try:
        coin = positions[0]['symbol']
        contracts = positions[0]['contracts']
        side = positions[0]['side']
        pnl = positions[0]['percentage']
        pnl = round(100*pnl, 2)

    except IndexError:
        side = 'none'
        pnl = 0
        contracts = 0
        ccc = ccc+1

        if ccc >= len(coins):
            ccc = 0
            ttc = ttc + 1

            if ttc >= len(tfs):
                ttc = 0
            tf = tc[ttc]
        coinName = cc[ccc]
        coin = str(f'{coinName}/USDT:USDT')

    try:
        candles = hashi(getData(coin, tf))

    except Exception as e:
        print(e)
        time.sleep(25)
        candles = hashi(getData(coin, tf))

    candles = candles.iloc[1:len(candles)-1].copy().reset_index(drop=True)

    o = getData(coin, tf)['open']
    c = getData(coin, tf)['close']
    h = getData(coin, tf)['high']
    l = getData(coin, tf)['low']
    close = candles['close'].iloc[-1]
    open = candles['open'].iloc[-1]
    green = open < close
    red = open > close

    print(f'{coin}: SIDE: {side}, CONTRACTS: {contracts}, PNL: {pnl}, TOTAL: {balance} -- Scanning for signals at timeframe {tf}...')

    if green:
        text = 'Green'
    elif red:
        text = 'Red'
    if bb.h(c) == 1:
        text = str(f'{text} / BB:H')
    elif bb.l(c) == 1:
        text = str(f'{text} / BB:L')
    text = str(f'{text} / RSI:{round(rsi(c,14), 1)}')
    if sma(c, 2) > sma(c, 3) > sma(c, 4):
        text = str(f'{text} / UP')
    elif sma(c, 2) < sma(c, 3) < sma(c, 4):
        text = str(f'{text} / DOWN')
    print(text)

    try:

        while pnl > takeProfit or pnl < stopLoss:
            print(f'stop-limit {pnl}')
            if side == 'long':
                order.sell()
            elif side == 'short':
                order.buy()
            elif side == 'none':
                exchange.cancel_all_orders()
                break
        if close > sma(c, 200):
            if (((rsi(c, 14) < 30) or green) and bb.l(c)) or (
                    sma(c, 2) > sma(c, 3) > sma(c, 5) > sma(c, 8) > sma(c, 13)):
                order.buy()
            elif (((rsi(c, 14) > 70) or red) and bb.h(c)) or (
                    sma(c, 2) < sma(c, 3) < sma(c, 5)) and side == 'long':
                exchange.cancel_all_orders()
                order.sell()
            time.sleep(10)
        elif close < sma(c, 200):
            if (((rsi(c, 14) > 70) or red) and bb.h(c)) or (
                    sma(c, 2) < sma(c, 3) < sma(c, 5) < sma(c, 8) < sma(c, 13)):
                order.sell()
            elif (((rsi(c, 14) < 30) or green) and bb.l(c)) or (
                    sma(c, 2) > sma(c, 3) > sma(c, 5)) and side == 'short':
                exchange.cancel_all_orders()
                order.buy()
            time.sleep(10)
    except Exception as e:
        print(e)
        time.sleep(30)
        exchange.cancel_all_orders()
