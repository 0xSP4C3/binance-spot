# !/usr/bin/python3
# -*- coding: utf-8 -*-
# Auth0r: ara_umi
# Email: 532990165@qq.com
# DateTime: 2022/6/5 14:06

# proxy for websocket
websocket_proxy = {
    "proxy_type": "http",
    "http_proxy_host": "127.0.0.1",
    "http_proxy_port": "7890"
}

# proxy for request
# requests_proxies = None
requests_proxies = {
    "https": "127.0.0.1:7890"
}

# binance api domain
domain = "https://api.binance.com/api/v3/"


# 有多个wss可以连接，/stream支持combine输入和简化数据返回
# wss_url = "wss://dstream.binance.com/stream/"
wss_url = "wss://stream.binance.com:9443/ws"
# wss_url = "wss://stream.binance.com:9443/stream"

LOG_LEVEL = "DEBUG"

# MySQL
DBHOST = "localhost"
DBUSER = "root"
DBPASS = "araumi"
DBNAME = "binance"

