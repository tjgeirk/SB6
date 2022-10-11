import datetime
import time
from ccxt import kucoinfutures as kucoin
from pandas import DataFrame as dataframe
from ta import trend, momentum, volatility, volume

API_KEY = ''
API_SECRET = ''
API_PASSWD = ''

stopLoss = -0.01
takeProfit = 0.1
leverage = 50
tf = '1m'
coins = ['BTC']
lotsPerTrade = 1

exchange = kucoin({
    'adjustForTimeDifference': True,
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSWD
})


print('\n'*100, 'TRADE AT YOUR OWN RISK. CRYPTOCURRENCY FUTURES TRADES ARE NOT FDIC INSURED. RESULTS ARE NOT GUARANTEED. POSITIONS MAY LOSE VALUE SUDDENLY AND WITHOUT WARNING. POSITINOS ARE SUBJECT TO LIQUIDATION. THERE ARE RISKS ASSOCIATED WITH ALL FORMS OF TRADING. IF YOU DON\'T UNDERSTAND THAT, THEN YOU SHOULD NOT BE TRADING IN THE FIRST PLACE. THIS SOFTWARE IS DEVELOPED FOR MY OWN USE, AND IS NOT TO BE INTERPRETED AS FINANCIAL ADVICE.')
time.sleep(2)
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

def sma(w):
    return trend.sma_indicator(getData(coin, tf)['close'], w).iloc[-1]

class order:
    def buy(side, contracts):
        ask = exchange.fetch_order_book(coin)['asks'][0][0]
        if side == 'short':
            amount = contracts
            params = {'reduceOnly': True, 'closeOrder': True}
        if side != 'short':
            amount = lotsPerTrade
            params = {'leverage': leverage}
        return exchange.create_limit_buy_order(coin, amount, ask, params=params)

    def sell(side, contracts):
        bid = exchange.fetch_order_book(coin)['bids'][0][0]
        if side == 'long':
            amount = contracts
            params = {'reduceOnly': True, 'closeOrder': True}
        if side != 'long':
            amount = lotsPerTrade
            params = {'leverage': leverage}
        return exchange.create_limit_sell_order(coin, amount, bid, params=params)


while True:
    positions = exchange.fetch_positions()
    for i, symbol in enumerate(coins):
        coin = str(f'{symbol}/USDT:USDT')
        try:
            pos = positions[i]
            pnl = pos['percentage']
            side = pos['side']
            contracts = pos['contracts']
        except Exception:
            pnl = 0
            side = 'none'
            contracts = 0
        try:
            while sma(2) > sma(3) > sma(5):
                if sma(2) < (sma(3) or sma(5)):
                    order.sell(side, contracts)
                    break
                else:
                    order.buy(side, contracts)

            while sma(2) < sma(3) < sma(5):
                if sma(2) > (sma(3) or sma(5)):
                    order.buy(side, contracts)
                    break
                else:
                    order.sell(side, contracts)
        except Exception as e:
            if len(exchange.fetch_open_orders()) > 10:
                exchange.cancel_all_orders()
                print(e)
