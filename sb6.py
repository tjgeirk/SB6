import datetime
import time
from ccxt import kucoinfutures as kucoin
from numpy import take
from pandas import DataFrame as dataframe
from ta import trend, momentum, volatility, volume

API_KEY = ''
API_SECRET = ''
API_PASSWD = ''

coins = ['ETH', 'XRP', 'ETC', 'BTC', 'LUNC', 'LUNA']
stopLoss = -0.03
takeProfit = 0.1

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

while True:
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

    def rsi(close, w):
        return momentum.rsi(close, w)

    def sma(close, w):
        return trend.sma_indicator(close, w)

    class bb:
        def h(close, window, deviations):
            return volatility.bollinger_hband(close, window, deviations)

        def l(close, window, deviations):
            return volatility.bollinger_lband(close, window, deviations)

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

    tfs = ['1m', '5m', '15m']

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

        hammer = (Close < Open and abs(Close - Low) > abs(High - Open)) or (
            Close > Open and abs(Open - Low) > abs(High - Close))

        invHammer = (Close < Open and abs(Close - Low) < abs(High - Open)) or (
            Close > Open and abs(Open - Low) < abs(High - Close))

        lowerband = bb.l(c, 20, 1).iloc[-1]
        upperband = bb.h(c, 20, 1).iloc[-1]
        sma10 = sma(c, 10).iloc[-1]

        try:
            if Open > upperband and invHammer and (side != 'long' or Low < sma10):
                order.sell()

            if Open < lowerband and hammer and (side != 'short' or High > sma10):
                order.buy()

            if pnl < stopLoss or pnl > takeProfit:
                if side == 'long':
                    order.sell()
                elif side == 'short':
                    order.buy()

        except Exception as e:
            print(e)
    for tf in tfs:
        positions = exchange.fetch_positions()
        balance = exchange.fetch_balance({'currency': 'USDT'})['free']['USDT']
        equity = exchange.fetch_balance()['info']['data']['accountEquity']
        leverage = 20 if tf == '1m' else 15 if tf == '5m' else 10
        for i, symbol in enumerate(coins):
            coin = str(f'{symbol}/USDT:USDT')
            try:
                pos = positions[i]
                pnl = pos['percentage']
                side = pos['side']
                contracts = pos['contracts']
                print(f'{tf} {coin} {side} {contracts} {pnl}% TOTAL: {equity}')
                bot()
            except Exception:
                pnl = 0
                side = 'none'
                contracts = 0
                print(f'{tf} {coin} {side} {contracts} {pnl}% TOTAL: {equity}')
                bot()
