# !/usr/bin/python3
# -*- coding: utf-8 -*-
# Auth0r: ara_umi
# Email: 532990165@qq.com
# DateTime: 2022/6/11 8:03
import json

import requests

from settings import requests_proxies


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


def getCoinsJson():
    with open("coins.json", "w") as f:
        json.dump(getCoinsList(), f, indent=4, sort_keys=True)


def readCoinsJson(path):
    with open(path, "r") as f:
        return json.load(f)


# get filtered json file from local json file by kw such as "USDT"
def getCoinsFilter(keyword):
    coins = readCoinsJson("coins.json")
    coins_filter = []
    for coin in coins:
        if keyword in coin:
            coins_filter.append(coin)
    with open(f"coins_filter_{keyword}.json", "w") as f:
        json.dump(coins_filter, f, indent=4, sort_keys=True)


if __name__ == '__main__':
    # getCoinsJson()
    getCoinsFilter("USDT")
