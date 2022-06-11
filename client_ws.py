# !/usr/bin/python3
# -*- coding: utf-8 -*-
# Auth0r: ara_umi
# Email: 532990165@qq.com
# DateTime: 2022/6/5 14:05

import json
import threading
import time
import traceback

import websocket

from getCoins import readCoinsJson
from log import Logger
from settings import wss_url, websocket_proxy


class BinanceWS(object):
    """
    base class
    """

    def __init__(self, url, logger, ensure_traceback=True):
        websocket.enableTrace(ensure_traceback)
        self.logger = logger
        self.ws = self._get_ws(url)

    def _get_ws(self, url):
        return websocket.WebSocketApp(url,
                                      on_open=self.on_open,
                                      on_close=self.on_close,
                                      on_message=self.on_message,
                                      on_error=self.on_error,
                                      on_ping=self.on_ping,
                                      on_cont_message=self.on_count_message,
                                      on_data=self.on_data
                                      )

    def run(self):
        self.ws.run_forever()

    def on_open(self, ws):
        self.logger.info("WS opened")

    def on_close(self, ws, status_code, message):
        self.logger.info(f"WS closed, status code:{status_code}, message:{message}")
        self.logger.info(f"### CLOSED ###")

    def on_data(self, ws, data, data_type, flag):
        """
        on_data: function
        Callback object which is called when a message received.
        This is called **before on_message or on_cont_message,
        and then on_message or on_cont_message is called.
        on_data has 4 argument.
        The 1st argument is this class object.
        The 2nd argument is utf-8 string which we get from the server.
        The 3rd argument is data type. ABNF.OPCODE_TEXT or ABNF.OPCODE_BINARY will be came.
        The 4th argument is continue flag. If 0, the data continue
        """
        pass

    def on_message(self, ws, data):
        print(data)

    def on_error(self, ws, error):
        info = traceback.format_exc()
        self.logger.error(error)
        self.logger.error(info)

    def on_ping(self, ws, timestamp):
        self.logger.info(f"Get ping")

    def send(self, data):
        pass

    def on_pong(self, ws):
        pass

    def on_count_message(self, ws):
        """
        on_cont_message: function
        Callback object which is called when a continuation
        frame is received.
        on_cont_message has 3 arguments.
        The 1st argument is this class object.
        The 2nd argument is utf-8 string which we get from the server.
        The 3rd argument is continue flag. if 0, the data continue
        to next frame data
        """
        pass


class KlineWS(BinanceWS):
    def __init__(self, url, logger, ensure_traceback=True):
        super(KlineWS, self).__init__(url, logger, ensure_traceback)

    @classmethod
    def set_subscribe_option(cls, coin_list: list, interval: str, number=20):
        """
        settings used for shape subscribe params
        number: numbers of symbols in the subscribe params sent to binance api
            too many symbols in a single params subscribed may not get response from the api successfully
            the subscribe function is actually doing a loop, in each loop subscribe several symbols
            recommend: 20-50
        interval:
        m -> minutes; h -> hours; d -> days; w -> weeks; M -> months
        eg: 1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M
        """
        cls.coin_list = coin_list
        cls.interval = interval
        cls.subscribe_number = number

    def run(self):
        super(KlineWS, self).run()

    def run_with_proxy(self, proxy: dict):
        """
        proxy eg:
        {
        "proxy_type": "http",
        "http_proxy_host": "127.0.0.1",
        "http_proxy_port": "7890"
        }
        """
        self.ws.run_forever(**proxy)

    def on_open(self, ws):
        def run(*args):
            super(KlineWS, self).on_open(ws)
            self.subscribe()

        threading.Thread(target=run).start()

    def subscribe(self):
        for i in range(0, len(self.coin_list), self.subscribe_number):

            params = []
            for symbol in self.coin_list[i:i + self.subscribe_number]:
                params.append(f"{symbol.lower()}@kline_{self.interval}")

            data = {
                "method": "SUBSCRIBE",
                "id": 1,
                "params": params
            }
            self.logger.info(f"Subscribe, symbols: {self.coin_list[i:i + self.subscribe_number]}")
            self.ws.send(json.dumps(data))

            # ws accept up to 5 messages per second including ping/pong, more than it will cause disconnection
            time.sleep(0.5)

    @staticmethod
    def _shape_params(coin_list):
        params = []
        for symbol in coin_list:
            params.append(symbol.lower() + "@kline_1m")
        return params

    def send(self, data):
        self.ws.send(json.dumps(data))

    def on_message(self, ws, data):
        data = json.loads(data)

        # when subscribe success, receive a message like "{"result":null,"id":1}"
        try:
            res = data["result"]
            if not res:
                self.logger.info("Subscribe success")
                return
        except KeyError:
            pass

        k = data["k"]
        is_close = k["x"]
        if is_close:
            shaped_data = {
                "event type": data["e"],
                # "event time": data["E"],
                "event time style": self.timestamp2strftime(data["E"]),
                "symbol": data["s"],
                # "start time": k["t"],
                "start time style": self.timestamp2strftime(k["t"]),
                # "close time": k["T"],
                "close time style": self.timestamp2strftime(k["T"]),
                # "interval": k["i"],
                # "first trade id": k["f"],
                # "last trade id": k["L"],
                "open price": k["o"],
                "close price": k["c"],
                "high price": k["h"],
                "low price": k["l"],
                "volume": k["v"],
                "trade numbers": k["n"],
                # "is close": k["x"],
                "quote volume": k["q"],
                "buying volume": k["V"],
                "buying quote volume": k["Q"],
                # "ignore": k["B"],
            }
            return self.dump_data(shaped_data)

    def dump_data(self, data):
        """
        called at the end of self.on_message
        """
        print(data)

    def on_error(self, ws, error):
        if type(error) == KeyboardInterrupt:
            self.ws.close()
            self.logger.info("KEYBOARD INTERRUPT, WEBSOCKET CLOSED")
        else:
            info = traceback.format_exc()
            self.logger.error(error)
            self.logger.error(info)

    @staticmethod
    def timestamp2strftime(ms: int):
        """
        unit: ms
        """
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ms * 1e-3))


def main():
    # get coin list
    coin_list = readCoinsJson("coins_filter_USDT.json")
    # get logger
    logger = Logger().get_logger()

    klines = KlineWS(wss_url, logger, ensure_traceback=False)
    # set params options
    klines.set_subscribe_option(coin_list, "1m", number=30)

    # if proxy
    klines.run_with_proxy(websocket_proxy)
    # direct
    # klines.run()


if __name__ == "__main__":
    main()
