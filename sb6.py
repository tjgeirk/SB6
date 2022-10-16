import datetime
import time

from ccxt import kucoinfutures as kucoin
from pandas import DataFrame as dataframe
from ta import momentum, trend

API_KEY = ''
API_SECRET = ''
API_PASSWD = ''
COINS = ['ETH']
STOPLOSS = 0.02
TAKEPROFIT = 0.05
TF = '1m'
LEVERAGE = 20
LOTSPERTRADE = 1
exchange = kucoin({
    'adjustForTimeDifference': True,
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSWD
})
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
            params = {'leverage': LEVERAGE, 'timeInForce': 'GTC'}
    elif type == 'sell':
        print(f'SELL {coin}')
        price = exchange.fetch_order_book(coin)['bids'][0][0]
        if side == 'long':
            amount = contracts
            params = {'reduceOnly': True,
                      'closeOrder': True, 'timeInForce': 'GTC'}
        elif side != 'long':
            amount = LOTSPERTRADE
            params = {'leverage': LEVERAGE, 'timeInForce': 'GTC'}
    return exchange.create_limit_order(coin, type, amount, price, params=params)


def ema(w):
    close = (getData(coin, TF)['close'])
    return trend.ema_indicator(close, w).iloc[-1]


def macd(slow, fast):
    close = (getData(coin, TF)['close'])
    return trend.macd(close, slow, fast).iloc[-1]


def bot():
    print(f'{TF} {coin} {side} {contracts} {round((100*pnl),2)}% TOTAL: {equity}')

    if macd(13, 21) < ema(8) and Open > Close:
        order('sell')
    elif macd(13, 21) > ema(8) and Open < Close:
        order('buy')
    elif ema(5) > ema(8) > ema(13) and Open < Close:
        order('buy')
    elif ema(5) < ema(8) < ema(13) and Open > Close:
        order('sell')
    elif side == 'long':
        if (ema(2) < ema(3)) or (
                ema(3) < ema(5)) or (
                macd(8, 13) < ema(5)):
            order('sell')
    elif side == 'short':
        if (ema(5) > ema(8)) or (
                ema(8) > ema(13)) or (
                macd(8, 13) > ema(5)):
            order('buy')


trail = 0
while True:
    try:
        positions = exchange.fetch_positions()
        equity = exchange.fetch_balance()['info']['data']['accountEquity']
        for symbol in COINS:
            coin = str(f'{symbol.upper()}/USDT:USDT')
            Open = (getData(coin, TF)['close'].iloc[-2] +
                    getData(coin, TF)['open'].iloc[-2])/2
            Close = (getData(coin, TF)['open'].iloc[-1]+getData(coin, TF)['high'].iloc[-1]+getData(
                coin, TF)['low'].iloc[-1]+getData(coin, TF)['close'].iloc[-1])/4
            pnl = float(0.0)
            contracts = int(0)
            side = str('none')
            for i in positions[0:]:
                if coin == i['symbol']:
                    pnl = i['percentage']
                    if pnl > trail:
                        trail = pnl
                        print(
                            f'TRAIL: {round(trail*100,2)}% -- STOP: {round(trail+STOPLOSS*100, 2)}%')
                    if pnl <= trail+STOPLOSS or pnl > TAKEPROFIT:
                        if side == 'long':
                            order('sell')
                        if side == 'short':
                            order('buy')
                    side = i['side']
                    contracts = i['contracts']
                    bot()
            bot()
    except Exception as e:
        exchange.cancel_all_orders()
        print(e)
