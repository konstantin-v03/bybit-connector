import requests
import base64
import config
from pybit import usdt_perpetual
import ast


def tg_send_message(text):
    return requests.get('https://api.telegram.org/bot' + config.BOT_TOKEN +
                        '/sendMessage?chat_id=' + config.CHAT_ID +
                        '&text=' + text + '').json()


def run(event, context):
    try:
        message = base64.b64decode(event['body']).decode('utf-8')
        dictionary = ast.literal_eval(message.replace("'", "\""))

        ticker = dictionary['ticker'].replace(".P", "")
        action = dictionary['action']
        contracts = dictionary['contracts']

        tg_send_message(f'{ticker} {action} {contracts}')

        session_auth = usdt_perpetual.HTTP(endpoint="https://api.bybit.com",
                                           api_key=config.API_KEY, api_secret=config.SECRET_KEY)

        response = ""

        if action == 'long':
            response = session_auth.place_active_order(
                symbol=ticker,
                side='Buy',
                order_type='Market',
                qty=contracts,
                time_in_force="GoodTillCancel",
                reduce_only=False,
                close_on_trigger=False)

        if action == 'Close entry(s) order long':
            response = session_auth.place_active_order(
                symbol=ticker,
                side='Sell',
                order_type='Market',
                qty=contracts,
                time_in_force="GoodTillCancel",
                reduce_only=True,
                close_on_trigger=False)

        if action == 'short':
            response = session_auth.place_active_order(
                symbol=ticker,
                side='Sell',
                order_type='Market',
                qty=contracts,
                time_in_force="GoodTillCancel",
                reduce_only=False,
                close_on_trigger=False)

        if action == 'Close entry(s) order short':
            response = session_auth.place_active_order(
                symbol=ticker,
                side='Buy',
                order_type='Market',
                qty=contracts,
                time_in_force="GoodTillCancel",
                reduce_only=True,
                close_on_trigger=False)

        tg_send_message(str(response))

        response = {'statusCode': 200, 'body': 'Message was successfully sent!'}
    except Exception as e:
        response = {'statusCode': 404, 'body': 'Something went wrong! ' + str(e)}

    tg_send_message(str(response))

    return response
