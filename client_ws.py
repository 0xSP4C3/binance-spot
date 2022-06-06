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
from log import logger
from settings import wss_url, websocket_proxy, ensure_traceback


class BinanceWebsocketClient(object):
    def __init__(self, dumper: type):
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
        self.dumper = dumper()

    def on_message(self, ws, message):
        """
        这个库里的on_message本身就是异步的(我也不知道到底是异步的还是并发的)，非常方便
        :param ws: websocket
        :param message: message type:str
        :return:
        """
        message = json.loads(message)
        # print(message)

        # 订阅成功后第一次返回为{'result': None, 'id': id}
        try:
            data = message["data"]
            self.dumper.dump_ws(data)
        except KeyError:
            if not message["result"]:
                self.logger.info("Subscribe success")

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

    def on_open(self, ws):
        print("Opened connection")
        self.logger.info("Opened connection")
        # 订阅ticker，会实时刷新，间隔1s
        data = {
            "method": "SUBSCRIBE",
            "id": 1,
            "params": ["!ticker"]
        }
        ws.send(json.dumps(data))

    def on_ping(self, ws, timestamp):
        self.logger.info(f"ping, {time.strftime('%X')}")

    def start(self):
        self.ws.run_forever(**websocket_proxy)

    def reboot(self):
        pass


if __name__ == "__main__":
    client = BinanceWebsocketClient(TickerPrice)
    client.start()
