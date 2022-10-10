#!/usr/local/bin/python3
#
from ccxt import kucoinfutures as kucoin
API_KEY = ''
API_SECRET = ''
API_PASSWD = ''

exchange = kucoin({
    'adjustForTimeDifference': True,
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSWD
})
while True:
    try:
        positions = exchange.fetch_positions()
        for coin in positions:
            if coin['side'] == 'long':
                exchange.create_market_sell_order(
                    coin['symbol'], coin['contracts'], {'reduceOnly': True, 'closeOrder': True})
            if coin['side'] == 'short':
                exchange.create_market_buy_order(
                    coin['symbol'], coin['contracts'], {'reduceOnly': True, 'closeOrder': True})
    except:
        exchange.cancel_all_orders()
