# !/usr/bin/python3
# -*- coding: utf-8 -*-
# Auth0r: ara_umi
# Email: 532990165@qq.com
# DateTime: 2022/6/7 0:05
from client_http import TickerPrice, per_5minutes, Timer

if __name__ == '__main__':
    ticker = TickerPrice()

    def main():
        data = ticker.query()
        ticker.dump2mysql(data)

    timer = Timer(main, per_5minutes)
    timer.run()
