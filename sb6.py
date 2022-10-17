import datetime
import time

import ta
from ccxt import kucoinfutures as kucoin
from pandas import DataFrame as dataframe
from ta import trend, volatility

API_KEY = ''
API_SECRET = ''
API_PASSWD = ''
SYMBOL = 'ETC'
STOPLOSS = 0.02
TAKEPROFIT = 0.05
TF = '1m'
LEVERAGE = 20
LOTSPERTRADE = 1000

exchange = kucoin({
    'adjustForTimeDifference': True,
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSWD
})
trail = 0
stop = trail - STOPLOSS
side = 'none'
contracts = 0
pnl = 0
coin = str(f'{SYMBOL}/USDT:USDT')
positions = exchange.fetch_positions()
equity = exchange.fetch_balance()['info']['data']['accountEquity']

print('\n'*100, 'TRADE AT YOUR OWN RISK. CRYPTOCURRENCY FUTURES TRADES ARE NOT FDIC INSURED. RESULTS ARE NOT GUARANTEED. POSITIONS MAY LOSE VALUE SUDDENLY AND WITHOUT WARNING. POSITINOS ARE SUBJECT TO LIQUIDATION. THERE ARE RISKS ASSOCIATED WITH ALL FORMS OF TRADING. IF YOU DON\'T UNDERSTAND THAT, THEN YOU SHOULD NOT BE TRADING IN THE FIRST PLACE. THIS SOFTWARE IS DEVELOPED FOR MY OWN USE, AND IS NOT TO BE INTERPRETED AS FINANCIAL ADVICE.')
time.sleep(1)
print('\n'*100, '...AND MOST OF ALL HAVE FUN!!\n')
time.sleep(1)
print('\n'*100)
exchange.load_markets()


def getData(coin, TF):
    data = exchange.fetch_ohlcv(coin, TF, limit=200)
    df = {}
    for i, col in enumerate(['date', 'open', 'high', 'low', 'close',
                                                     'volume']):
        df[col] = []
        for row in data:
            if col == 'date':
                df[col].append(
                    datetime.datetime.fromtimestamp(row[i] / 1000))
            else:
                df[col].append(row[i])
        DF = dataframe(df)
    return DF


def order(type):
    if type == 'buy':
        print(f'BUY {coin}')
        price = exchange.fetch_order_book(coin)['asks'][0][0]
        if side == 'short':
            amount = contracts
            params = {'reduceOnly': True,
                      'closeOrder': True, 'timeInForce': 'GTC'}
        elif side != 'short':
            amount = LOTSPERTRADE
            params = {'leverage': LEVERAGE, 'timeInForce': 'IOC'}
    elif type == 'sell':
        print(f'SELL {coin}')
        price = exchange.fetch_order_book(coin)['bids'][0][0]
        if side == 'long':
            amount = contracts
            params = {'reduceOnly': True,
                      'closeOrder': True, 'timeInForce': 'GTC'}
        elif side != 'long':
            amount = LOTSPERTRADE
            params = {'leverage': LEVERAGE, 'timeInForce': 'IOC'}
    return exchange.create_limit_order(coin, type, amount, price, params=params)


def ema(w):
    return trend.ema_indicator((getData(coin, TF)['close']), w).iloc[-1]


def macd(fast, slow, signal):
    return 1 if (ema(fast) - ema(slow)) < ema(signal) else -1 if (ema(fast) - ema(slow)) > ema(signal) else 0


class bb:
    def h(window, deviations):
        return volatility.bollinger_hband(getData(coin, TF)['close'], window, deviations).iloc[-1]

    def l(window, deviations):
        return volatility.bollinger_lband(getData(coin, TF)['close'], window, deviations).iloc[-1]


def bot():
    if Open < bb.l(20, 1) and Close > Open:
        order('buy')
    elif Open > bb.h(20, 1) and Close < Open:
        order('sell')
    if side == 'long' and Close < Open and lastClose < lastOpen:
        order('sell')
    if side == 'short' and Close > Open and lastClose > lastOpen:
        order('buy')


while True:
    try:
        Open = (getData(coin, TF)['close'].iloc[-2] +
                getData(coin, TF)['open'].iloc[-2])/2
        Close = (getData(coin, TF)['open'].iloc[-1] +
                 getData(coin, TF)['high'].iloc[-1] +
                 getData(coin, TF)['low'].iloc[-1] +
                 getData(coin, TF)['close'].iloc[-1])/4
        lastOpen = (getData(coin, TF)['close'].iloc[-3] +
                    getData(coin, TF)['open'].iloc[-3])/2
        lastClose = (getData(coin, TF)['open'].iloc[-2] +
                     getData(coin, TF)['high'].iloc[-2] +
                     getData(coin, TF)['low'].iloc[-2] +
                     getData(coin, TF)['close'].iloc[-2])/4
        High = getData(coin, TF)['high'].iloc[-1]
        Low = getData(coin, TF)['low'].iloc[-1]

        try:
            for ii, i in enumerate(positions):
                if coin == i['symbol']:
                    pnl = i['percentage']
                    side = i['side']
                    contracts = i['contracts']
        except Exception:
            pnl = 0.0
            contracts = 0
            side = 'none'
            trail = 0

        if pnl > trail:
            trail = pnl
        stop = trail - abs(STOPLOSS)
        print(
            f'TRAIL: {round(trail*100,2)}% -- STOP: {round(stop*100, 2)}%')
        if pnl <= stop:
            if side == 'long':
                order('sell')
            if side == 'short':
                order('buy')
        print(
            f'{TF} {coin} {side} {contracts} {round((100*pnl),2)}% TOTAL: {equity}')
        bot()
    except Exception as e:
        print(e)
        time.sleep(10)
