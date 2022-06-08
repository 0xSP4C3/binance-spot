# !/usr/bin/python3
# -*- coding: utf-8 -*-
# Auth0r: ara_umi
# Email: 532990165@qq.com
# DateTime: 2022/6/7 0:05
from client_http import TickerPrice, per_5minutes, Timer, per_minute

if __name__ == '__main__':
    ticker = TickerPrice()

    def main():
        try:
            data = ticker.query()
            ticker.dump2mysql(data)
        except Exception as e:
            print(e)
            ticker.dumper.db.close()

    timer = Timer(main, per_minute)
    timer.run()
