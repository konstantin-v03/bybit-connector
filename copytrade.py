import requests
import hashlib
import hmac
import config
import time
import json
import base64
import ast

httpClient = requests.Session()
recv_window = str(5000)
endpoint = "https://api.bybit.com"


def http_request(suffix, method, **kwargs):
    if method == "POST":
        data = str(kwargs).replace("\'", "\"")
    else:
        arguments = []

        for key in kwargs:
            arguments.append(str(key) + "=" + str(kwargs[key]))

        data = '&'.join(arguments)

    timestamp = str(int(time.time() * 10 ** 3))

    signature = hmac.new(bytes(config.SECRET_KEY, "utf-8"),
                         (str(timestamp) + config.API_KEY + recv_window + data).encode("utf-8"),
                         hashlib.sha256).hexdigest()

    headers = {
        'X-BAPI-API-KEY': config.API_KEY,
        'X-BAPI-SIGN': signature,
        'X-BAPI-SIGN-TYPE': '2',
        'X-BAPI-TIMESTAMP': timestamp,
        'X-BAPI-RECV-WINDOW': recv_window,
        'Content-Type': 'application/json'
    }

    if method == "POST":
        response = httpClient.request(method, endpoint + suffix, headers=headers, data=data)
    else:
        response = httpClient.request(method, endpoint + suffix + "?" + data, headers=headers)

    return response


def open_long_market(symbol, qty):
    return http_request("/contract/v3/private/copytrading/order/create", "POST",
                        symbol=symbol,
                        side="Buy",
                        orderType="Market",
                        qty=qty)


def open_short_market(symbol, qty):
    return http_request("/contract/v3/private/copytrading/order/create", "POST",
                        symbol=symbol,
                        side="Sell",
                        orderType="Market",
                        qty=qty)


def close_long_market(symbol):
    return close_position_by_idxs(get_position_idxs_by_symbol(symbol, "Buy"))


def close_short_market(symbol):
    return close_position_by_idxs(get_position_idxs_by_symbol(symbol, "Sell"))


def get_position_idxs_by_symbol(symbol, side):
    response = http_request("/contract/v3/private/copytrading/position/list", "GET", symbol="BTCUSDT").text
    response_json = json.loads(response)

    positions_idxs = []

    for position in response_json["result"]["list"]:
        if position["symbol"] == symbol and position["side"] == side:
            positions_idxs.append(position["positionIdx"])

    return positions_idxs


def close_position_by_idxs(positions_idxs):
    response = "Nothing to close"

    for positions_idx in positions_idxs:
        response = http_request("/contract/v3/private/copytrading/position/close", "POST",
                                symbol="BTCUSDT",
                                positionIdx=positions_idx)

    return response


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

        response = ""

        if action == 'long':
            response = open_long_market(ticker, contracts)

        if action == 'Close entry(s) order long':
            response = close_long_market(ticker)

        if action == 'short':
            response = open_short_market(ticker, contracts)

        if action == 'Close entry(s) order short':
            response = close_short_market(ticker)

        tg_send_message(str(response.text))

        response = {'statusCode': 200, 'body': 'Message was successfully sent!'}
    except Exception as e:
        response = {'statusCode': 404, 'body': 'Something went wrong! ' + str(e)}

    tg_send_message(str(response))

    return response
