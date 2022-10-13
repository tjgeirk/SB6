import datetime
import time
from ta import trend, momentum, volatility
from pandas import DataFrame as dataframe
from ccxt import kucoinfutures as kucoin

API_KEY = ''
API_SECRET = ''
API_PASSWD = ''

coins = ['ETH', 'XRP', 'ETC', 'BTC', 'LUNC', 'LUNA']
stopLoss = -0.03
takeProfit = 0.1
tf = '1h'
lotsPerTrade = 10

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

def getData(coin, tf):
    data = exchange.fetch_ohlcv(coin, tf, limit=500)
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

def rsi(w):
    return momentum.rsi(getData(coin, tf)['close'], w).iloc[-1]

def sma(w):
    return trend.sma_indicator(getData(coin, tf)['close'], w).iloc[-1]

def ema(w):
    return trend.ema_indicator(getData(coin, tf)['close'], w).iloc[-1]

class bb:
    def h():
        return volatility.bollinger_hband(getData(coin, tf)['close'], 20, 2).iloc[-1]

    def l():
        return volatility.bollinger_lband(getData(coin, tf)['close'], 20, 2).iloc[-1]

class order:
    def buy():
        ask = exchange.fetch_order_book(coin)['bids'][0][0]
        if side == 'short':
            amount = contracts
            params = {'reduceOnly': True, 'closeOrder': True}
        if side != 'short':
            amount = lotsPerTrade
            params = {'leverage': leverage}

        return exchange.create_limit_buy_order(coin, amount, ask, params=params)

    def sell():
        bid = exchange.fetch_order_book(coin)['asks'][0][0]
        if side == 'long':
            amount = contracts
            params = {'reduceOnly': True, 'closeOrder': True}
        if side != 'long':
            amount = lotsPerTrade
            params = {'leverage': leverage}
        return exchange.create_limit_sell_order(coin, amount, bid, params=params)

while True:
    positions = exchange.fetch_positions()
    balance = exchange.fetch_balance({'currency': 'USDT'})['free']['USDT']
    equity = exchange.fetch_balance()['info']['data']['accountEquity']

    for symbol in coins:
        coin = str(f'{symbol}/USDT:USDT')
        pnl = side = contracts = 0
        for i in positions[0:]:
            if coin == i['symbol']:
                pnl = i['percentage']
                side = i['side']
                contracts = i['contracts']
        leverage = 20 if tf == '1m' else 15 if tf == '5m' else 10
        print(f'{tf} {coin} {side} {contracts} {pnl}% TOTAL: {equity}')

        h = getData(coin, tf)['high']
        l = getData(coin, tf)['low']
        c = getData(coin, tf)['close']
        o = getData(coin, tf)['open']
        v = getData(coin, tf)['volume']

        Close = c.iloc[-1]
        High = h.iloc[-1]
        Low = l.iloc[-1]
        Open = o.iloc[-1]
        macd = ema(12) - ema(26)
        signal = ema(9)
        try:
            if sma(200) < Close or side == 'short':
                if Open < bb.l() and Close > ema(8):
                    order.buy()
                if signal < macd and Close > ema(8):
                    order.buy()  
                if pnl < stopLoss or pnl > takeProfit:
                    order.buy()
            if sma(200) > Close or side == 'long':
                if signal > macd and Close < ema(8):
                    order.sell()
                if Open > bb.h() and Close < ema(8):
                    order.sell()
                if pnl < stopLoss or pnl > takeProfit:
                    order.sell()
        except Exception as e:
            print(e)

#    import talib
#    candle_names = talib.get_function_groups()['Pattern Recognition']
#    bear = bull = 0
#    for candle in candle_names:
#        if getattr(talib, candle)(o, h, l, c).iloc[-1] < 0:
#            bear += 1
#            print('bear: ', bear)
#        elif getattr(talib, candle)(o, h, l, c).iloc[-1] > 0:
#            bull += 1
#            print('bull: ', bull)
