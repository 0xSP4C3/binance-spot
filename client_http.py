# !/usr/bin/python3
# -*- coding: utf-8 -*-
# Auth0r: ara_umi
# Email: 532990165@qq.com
# DateTime: 2022/6/6 11:45

# !/usr/bin/python3
# -*- coding: utf-8 -*-
import json
import os
import time
from abc import ABCMeta, abstractmethod
from threading import Thread, Event
from typing import Callable
from urllib.parse import urljoin, urlencode

import requests

from log import MyLogger
from settings import requests_proxies, domain


def per_second(timestamp):
    return True


def per_10seconds(timestamp):
    if timestamp % 10 == 0:
        return True


def per_30seconds(timestamp):
    pass


def per_minute(timestamp):
    if timestamp % 60 == 0:
        return True


def per_5minutes(timestamp):
    if timestamp % 300 == 0:
        return True


class Timer(object):
    def __init__(self, function, strategy: Callable):
        """
        :param function: the target function that needs to be executed
        :param strategy: function to decide when does the Timer send signals, default argument:timestamp
        """
        self.logger = logger
        self.function = function
        self.strategy = strategy
        self.time_style = "%Y-%m-%d %H:%M:%S"
        self.event = Event()
        self.event.clear()

    def time_sender(self):
        former = None
        while True:
            timestamp = time.time()
            timestamp_int = int(timestamp)
            timeSec = time.time() - timestamp_int
            if former != timestamp_int:
                former = timestamp_int
                if self.strategy(former):
                    # self.logger.info(f"Timer on, delay:{timeSec}")
                    self.logger.info(f"Timer on")
                    self.event.set()

    def myFunction(self):
        while True:
            self.event.wait()
            self.function()
            self.event.clear()

    def run(self):
        timer_thread = Thread(target=self.time_sender)
        time_function = Thread(target=self.myFunction)
        timer_thread.start()
        self.logger.info("Timer thread start")

        time_function.start()
        self.logger.info("Function thread start")

        timer_thread.join()
        time_function.join()


class BinanceRequests(metaclass=ABCMeta):
    domain = domain

    def __init__(self):
        self.logger = MyLogger().logger
        # self.test_ping()

    def test_ping(self):
        """
        return {} if success
        """
        if self.requests_get("ping", ""):
            self.logger.error("TEST PING FAILED")
            raise ValueError
        else:
            self.logger.info("TEST PING SUCCESS")
            return True

    def requests_get(self, api, querystring: str):
        """
        request url = domain + api + querystring
        query: str
        """
        url = urljoin(domain, api) + querystring
        self.logger.info(f"Request, method:GET url:{url}")

        if requests_proxies:
            return requests.get(url, proxies=requests_proxies).json()
        else:
            return requests.get(url).json()

    def requests_post(self):
        pass

    @staticmethod
    def shape_query(query_dict):
        """
        pay attention to the format of the key eg: "startTime" not "start_time" or "start time"
        see more at https://binance-connector.readthedocs.io/en/latest/binance.spot.html#
        query: dict or Null if no params needed
        """

        if query_dict:
            # query_dict = dict(sorted(query_dict.items(), key=lambda x: x[0]))
            querystring = "?" + urlencode(query_dict)
        else:
            querystring = ""

        return querystring

    @staticmethod
    def timestamp2strftime(ms: int):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ms * 1e-3))

    def shape_query_dict(self, *args, **kwargs):
        pass

    @abstractmethod
    def query(self, *args, **kwargs):
        pass


class Klines(BinanceRequests):
    def __init__(self, symbol, interval, *, limit=None, start_time=None, end_time=None):
        super(Klines, self).__init__()
        self.api = "klines"
        self.query_dict = self.shape_query_dict(symbol, interval, limit, start_time, end_time)

    @staticmethod
    def shape_query_dict(symbol, interval, limit, start_time, end_time):
        """
        shape query dict by init arguments
        """
        query_dict = {
            # necessary
            "symbol": symbol,
            "interval": interval,
        }
        if limit:
            # default 500
            query_dict["limit"] = limit
        if start_time:
            query_dict["startTime"] = start_time,
        if end_time:
            query_dict["endTime"] = end_time

        return query_dict

    def query(self):
        startTime = time.time()
        querystring = self.shape_query(self.query_dict)
        tries = 0
        while True:
            try:
                response = self.requests_get(self.api, querystring)
                data = self.format_response(response)
                self.logger.info(f"Get response success, cost time:{time.time() - startTime}")
                return data
            except Exception as e:
                tries += 1
                self.logger.error(e)
                self.logger.info(f"retries:{tries}")

    def format_response(self, response):
        data = []
        for item in response:
            data.append({
                "open time": item[0],
                "open time style": self.timestamp2strftime(item[0]),
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5]),
                "close time": item[6],
                "close time style": self.timestamp2strftime(item[6]),
                "quote volume": float(item[7]),
                "trade numbers": item[8],
                "volume buying": float(item[9]),
                "quote volume buying": float(item[10])
            })
        return data

    def dump2mysql(self):
        pass

    def dump2json(self, data, filepath):
        with open(f"{filepath}", "w") as f:
            try:
                json.dump(data, f, indent=4)
                self.logger.info(f"Dump to json success, path:{filepath}")
            except Exception as e:
                self.logger.error(f"Dump error:{e}")


class TickerPrice(BinanceRequests):
    def __init__(self, symbol=""):
        super(TickerPrice, self).__init__()
        self.api = "ticker/price"
        self.query_dict = self.shape_query_dict(symbol)
        # self.dumper = dumper.TickerPrice()

    @staticmethod
    def shape_query_dict(symbol):
        if not symbol:
            query_dict = {}
        elif type(symbol) == str:
            query_dict = {"symbol": symbol}
        elif type(symbol) == list:
            symbol = str(symbol).replace("\'", "\"").replace(" ", "")
            query_dict = {"symbols": symbol}
        else:
            raise ValueError("Incorrect symbol")

        return query_dict

    def query(self):
        startTime = time.time()
        querystring = self.shape_query(self.query_dict)
        tries = 0
        while True:
            try:
                query_timestamp = time.time()
                response = self.requests_get(self.api, querystring)
                data = self.format_response(response, query_timestamp)
                self.logger.info(f"Get response success, cost time:{time.time() - startTime}")
                return data
            except Exception as e:
                tries += 1
                self.logger.error(e)
                self.logger.info(f"retries:{tries}")

    def format_response(self, response, timestamp):
        data = []
        for item in response:
            data.append({
                "SYMBOL": item["symbol"],
                "PRICE": item["price"],
                "TIMESTAMP": int(timestamp),
                "DATETIME": self.timestamp2strftime(timestamp * 1e3)
            })
        return data

    def dump2json(self, data, filepath):
        pass

    def dump2mysql(self, data):
        startTime = time.time()
        self.dumper.dump_http(data)
        self.logger.info(f"Dump data success, cost time:{time.time() - startTime}")


def getCoinsList():
    data = requests.get("https://api.binance.com/api/v3/ticker/price", proxies=requests_proxies).json()
    coin_list = []
    for item in data:
        coin_list.append(item["symbol"])
    return coin_list


def getCoinsGenerator():
    data = requests.get("https://api.binance.com/api/v3/ticker/price", proxies=requests_proxies).json()
    for item in data:
        yield item["symbol"]


# get Klines data for several symbols and dump into json, limit 1000days
def getKlinesData():
    for symbol in getCoinsGenerator():
        klines = Klines(symbol, "1d", limit=1000)

        # mkdir for jsons
        root = os.path.dirname(__file__) + "\\1000days"
        if not os.path.exists(root):
            os.mkdir(root)
        filename = symbol + ".json"
        filepath = root + "\\" + filename

        data = klines.query()
        klines.dump2json(data, filepath)


# get Klines data for specific symbols and dump into json, all time
def getKlinesDataAllTime(symbol, interval):
    # mkdir for json
    root = os.path.dirname(__file__) + f"\\AllTime_{interval}"
    if not os.path.exists(root):
        os.mkdir(root)
    filename = symbol + ".json"
    filepath = root + "\\" + filename

    endTime = int(time.time() * 1e3)
    data_all = []
    while True:
        klines = Klines(symbol, interval, end_time=endTime, limit=1000)
        data = klines.query()
        if endTime == data[0]["open time"]:
            break
        endTime = data[0]["open time"]
        data_all.extend(data)

    data_all.sort(key=lambda x: x["open time"])
    klines.dump2json(data_all, filepath)


# get Klines data for all symbols from json file and dump into jsons, all time
def getKlinesDataAllTime_all(coins_json, interval: str):
    with open(coins_json, "r") as f:
        coins = json.load(f)

    for symbol in coins:
        getKlinesDataAllTime(symbol, interval)


if __name__ == '__main__':
    # ticker = Klines("BTCUSDT", "4h", limit=10)
    # data_test = ticker.query()
    # ticker.dump2mysql(data_test)

    getKlinesDataAllTime("BTCUSDT", "4h")

    # getKlinesDataAllTime_all("coins_filter_USDT.json", "4h")
