from ta import trend, momentum, volatility
from pandas import DataFrame as dataframe
import ccxt
import time
import datetime
API_KEY = ''
API_SECRET = ''
API_PASSWD = ''

coins = ['ADA', 'APE', 'BTC', 'ETC', 'ETH', 'LUNA', 'LUNC']
tfs = ['5m', '15m', '30m', '1h', '2h', '4h']
lotsPerTrade = 1
leverage = 20
stopLoss = -10
takeProfit = 5

## end of config ##

tc = dict(enumerate(tfs, 0))
ttc = int(len(tfs)-1)
tf = tc[ttc]
cc = dict(enumerate(coins, 0))
ccc = int(len(coins)-1)
coinName = cc[ccc]
side = 'none'
stopLoss = int(-abs(stopLoss))
takeprofit = int(abs(takeProfit))
exchange = ccxt.kucoinfutures({
    'adjustForTimeDifference': True,
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSWD
})


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


def rsi(w):
    return momentum.rsi(candles['close'], w).iloc[-1]


def sma(w):
    return trend.sma_indicator(candles['close'], w).iloc[-1]


class kc:
    def h():
        return volatility.keltner_channel_hband_indicator()(
            candles['high'], candles['low'], candles['close'], 20, 10, False, False).iloc[-1]

    def l():
        return volatility.keltner_channel_lband_indicator()(
            candles['high'], candles['low'], candles['close'], 20, 10, False, False).iloc[-1]


class order:
    def buy():
        bid = exchange.fetch_order_book(coin)['bids'][0][0]
        if side == 'short':
            qty = contracts
            params = {'reduceOnly': True, 'closeOrder': True}
        else:
            qty = lotsPerTrade
            params = {'leverage': leverage}
        return exchange.create_limit_buy_order(coin, qty, bid, params=params)

    def sell():
        ask = exchange.fetch_order_book(coin)['asks'][0][0]
        if side == 'long':
            qty = contracts
            params = {'reduceOnly': True, 'closeOrder': True}
        else:
            qty = lotsPerTrade
            params = {'leverage': leverage}
        return exchange.create_limit_sell_order(coin, qty, ask, params=params)


while True:
    exchange.load_markets()
    balance = round(
        exchange.fetch_balance()['info']['data']['accountEquity'], 2)
    positions = exchange.fetch_positions()
    try:
        contracts = positions[0]['contracts']
        side = positions[0]['side']
        pnl = positions[0]['percentage']
        pnl = round(100*pnl, 2)
    except IndexError:
        side = 'none'
        pnl = 0
        contracts = 0
    if side == 'none':
        ttc = ttc + 1
        if ttc >= len(tfs):
            ttc = 0
            ccc = ccc + 1
            if ccc >= len(coins):
                ccc = 0
            coinName = cc[ccc]
        tf = tc[ttc]
    coin = str(f'{coinName}/USDT:USDT')
    print(f'{coin}: SIDE: {side}, CONTRACTS: {contracts}, PNL: {pnl}, TOTAL: {balance} -- Scanning for signals at timeframe {tf}...')

    try:
        candles = hashi(getData(coin, tf))
    except:
        time.sleep(25)
        candles = hashi(getData(coin, tf))
    candles = candles.iloc[1:len(candles)-1].copy().reset_index(drop=True)
    O = candles['open']
    C = candles['close']
    green = C.iloc[-1] > O.iloc[-1] or C.iloc[-2] > O.iloc[-2]
    red = C.iloc[-1] < O.iloc[-1] or C.iloc[-2] < O.iloc[-2]
    high = candles['high'].iloc[-1] or candles['high'].iloc[-2]
    low = candles['low'].iloc[-1] or candles['low'].iloc[-2]
    close = C.iloc[-1]

    try:
        if pnl > takeProfit or pnl < stopLoss:
            print(f'stop-limit {pnl}')
            if side == 'long':
                order.sell()
            elif side == 'short':
                order.buy()
            time.sleep(30)

        if close > sma(200):
            print('Looking for buy signals')
            if (rsi(14) < 30 and kc.l()) or sma(2) > sma(3) > sma(5):
                order.buy
            if side == 'long' and (
                    (rsi(14) > 70 and kc.h()) or sma(2) < sma(3) < sma(5)):
                order.sell

        elif close < sma(200):
            print('Looking for sell signals')
            if (rsi(14) > 70 and kc.h()) or sma(2) < sma(3) < sma(5):
                order.sell
            if side == 'short' and (
                    (rsi(14) < 30 and kc.l()) or sma(2) > sma(3) > sma(5)):
                order.buy

    except Exception as e:
        print(e)
        time.sleep(5)
