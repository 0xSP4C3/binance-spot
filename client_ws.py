# !/usr/bin/python3
# -*- coding: utf-8 -*-
# Auth0r: ara_umi
# Email: 532990165@qq.com
# DateTime: 2022/6/5 14:05
import json
import time
import traceback

import websocket

from dumper import TickerPrice
from getCoins import readCoinsJson
from log import logger
from settings import wss_url, websocket_proxy, ensure_traceback


class BinanceWebsocketClient(object):
    def __init__(self):
        """
        输入一个基类为Base的dumper用于数据存储，该类将会在init中实例化
        根据输入类的不同，更改数据的存储方式
        """
        websocket.enableTrace(ensure_traceback)
        self.ws = websocket.WebSocketApp(wss_url,
                                         on_open=self.on_open,
                                         on_close=self.on_close,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_ping=self.on_ping,
                                         )
        self.logger = logger
        # self.dumper = dumper()
        # self.coins = readCoinsJson("coins.json")
        self.coins = readCoinsJson("coins_filter_USDT.json")

    @staticmethod
    def timestamp2strftime(ms: int):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ms * 1e-3))

    def on_open(self, ws):
        self.logger.info("Opened connection")
        self.subscribe(ws)

    def subscribe(self, ws):
        params = self._shape_params()
        data = {
            "method": "SUBSCRIBE",
            "id": 1,
            "params": params
        }
        print(data)
        ws.send(json.dumps(data))

    def _shape_params(self):
        params = []
        for symbol in self.coins[:20]:
            params.append(symbol.lower() + "@kline_1m")
        return params

    def on_message(self, ws, message):
        """
        这个库里的on_message本身就是异步的(我也不知道到底是异步的还是并发的)，非常方便
        :param ws: websocket
        :param message: message type:str
        :return:
        """
        message = json.loads(message)

        try:
            res = message["result"]
            if not res:
                self.logger.info("Subscribe success")
                return
        except KeyError:
            pass

        k = message["k"]
        if k["x"]:
            data = {
                "event type": message["e"],
                # "event time": message["E"],
                "event time style": self.timestamp2strftime(message["E"]),
                "symbol": message["s"],
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
            print(time.localtime().tm_min, ":", time.localtime().tm_sec)
            print(data)
            print("-------------------------------")

        # 订阅成功后第一次返回为{'result': None, 'id': id}
        # try:
        #     data = message["data"]
        #     self.dumper.dump_ws(data)
        # except KeyError:
        #     if not message["result"]:
        #         self.logger.info("Subscribe success")

    def on_error(self, ws, error):
        if type(error) == KeyboardInterrupt:
            self.ws.close()
            self.logger.info("KEYBOARD INTERRUPT, WEBSOCKET CLOSED")
        else:
            info = traceback.format_exc()
            self.logger.error(error)
            self.logger.error(info)

    def on_close(self, ws, close_status_code, close_msg):
        self.ws.close()
        print("### Closed ###")

    def on_ping(self, ws, timestamp):
        self.logger.info(f"ping, {time.strftime('%X')}")

    def start(self):
        self.ws.run_forever(**websocket_proxy)

    def reboot(self):
        pass


if __name__ == "__main__":
    client = BinanceWebsocketClient()
    client.start()
