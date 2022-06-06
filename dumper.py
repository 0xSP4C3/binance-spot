# !/usr/bin/python3
# -*- coding: utf-8 -*-
# Auth0r: ara_umi
# Email: 532990165@qq.com
# DateTime: 2022/6/5 16:37
import time

import pymysql
import requests
from pymysql.constants import CLIENT

from log import logger
from settings import DBNAME, DBPASS, DBUSER, DBHOST

# 默认表名，为了方便修改就创建个变量
table_coin = "COIN"
table_info = "INFO"


class Base(object):
    def __init__(self):
        self.db = self._connect_mysql()
        self.logger = logger

    # 连接数据库
    def _connect_mysql(self):
        try:
            db = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASS, client_flag=CLIENT.MULTI_STATEMENTS)
            print(f"CONNECTION SUCCESS\n\tHOST:{DBHOST}\n\tUSER:{DBUSER}")
            return db
        except pymysql.Error as e:
            self.logger.error(e)
            print("CONNECTION FAILED", str(e))

    # 执行语句事务
    def execute_sql(self, sql, cur):
        try:
            self.db.begin()
            cur.execute(sql)
            self.db.commit()
        except pymysql.Error as e:
            self.logger.error(f"{e}, sql:{sql}")
            self.db.rollback()

    def dump_ws(self, data):
        print("Undefined dump method")

    # 释放资源
    def release(self, cur):
        cur.close()
        self.db.close()


class Initor(Base):
    """
    用于初始化数据库，功能集成在database_init中，包含以下内容：
    检查并创建数据库binance
    删除并重新创建表格：币种表、详情表
    发送请求获取所有币种，并将所有币种写入币种表中
    """

    def __init__(self):
        super(Initor, self).__init__()

    def _creat_database(self):
        """
        创建数据库，命名为binance，若已存在则跳过
        """
        self.cur = self.db.cursor()
        sql = f"CREATE DATABASE IF NOT EXISTS {DBNAME};USE {DBNAME};" \
              f"USE {DBNAME};"
        self.execute_sql(sql, self.cur)

    def _create_table(self):
        """
        该操作会删除原有的表格
        """

        # 删除旧表
        sql = f"DROP TABLE IF EXISTS {table_info};" \
              f"DROP TABLE IF EXISTS {table_coin};"
        self.execute_sql(sql, self.cur)

        # 创建币种表
        sql = f"CREATE TABLE {table_coin} (" \
              f"`SYMBOL` VARCHAR (20) PRIMARY KEY NOT NULL)" \
              f"ENGINE=InnoDB DEFAULT CHARSET=utf8;"
        self.execute_sql(sql, self.cur)

        # 创建详情表
        """
        索引的事情我不太懂，就创的简单索引
        关于是否需要时间戳，我这里默认时间戳单位是ms，就是从API过来的数据原封不动
        可能会出现有相同DATETIME的情况，可以使用时间戳判断先后
        这里的时间统一指的都是从binance的API接收到的数据里的时间，不是执行sql的时间
        如果想要比对同执行sql的时间的误差，可以加上：f"`TIMESTAMP_LOAD` TIMESTAMP DEFAULT CURRENT_TIMESTAMP, " 
        """
        sql = f"CREATE TABLE {table_info} (" \
              f"`ID` INT(15) PRIMARY KEY NOT NULL AUTO_INCREMENT, " \
              f"`SYMBOL` VARCHAR (20) NOT NULL, " \
              f"`PRICE` DOUBLE (15,5) DEFAULT NULL, " \
              f"`DATETIME` DATETIME NOT NULL, " \
              f"`TIMESTAMP` BIGINT(15) NOT NULL, " \
              f"INDEX(SYMBOL)," \
              f"CONSTRAINT FK_SYMBOL_COIN FOREIGN KEY (SYMBOL) REFERENCES {table_coin}(SYMBOL))" \
              f"ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;"
        self.execute_sql(sql, self.cur)

    @staticmethod
    def _get_coins():
        """
        获取所有币种用于输入到COIN表中，默认使用了proxy，实际使用时请修改
        :return: generator
        """
        proxies = {
            "https": "127.0.0.1:7890"
        }
        response = requests.get("https://api.binance.com/api/v3/ticker/price", proxies=proxies).json()
        return [item["symbol"] for item in response]

    def _fill_coin(self):
        """
        初始化币种信息
        """
        sql = ""
        for symbol in self._get_coins():
            sql += f"INSERT INTO {table_coin} (SYMBOL) VALUES (\"{symbol}\");"
        self.execute_sql(sql, self.cur)

    def database_init(self):
        """
        由于初始化会删除所有表格，需要简单确认
        """
        if input("ENTERING `INITDATABASE` TO COMFIRM:\n") == "INITDATABASE":
            self._creat_database()
            self._create_table()
            self._fill_coin()
            print("SUCCESSFULLY INIT DATABASE")
        else:
            print("BAD INPUT")
            return


class TickerPrice(Base):
    """
    专门用于实时价格插入数据库的类
    """

    def __init__(self):
        super(TickerPrice, self).__init__()
        self.cur = self.db.cursor()
        self._select_database()

    # 选择数据库
    def _select_database(self):
        sql = f"USE {DBNAME}"
        self.execute_sql(sql, self.cur)

    # 表格数据插入
    def _insert(self, symbol, price, datetime, timestamp):
        sql = f"INSERT INTO {table_info} (SYMBOL, PRICE, DATETIME, TIMESTAMP) " \
              f"VALUES (\"{symbol}\", \"{price}\", \"{datetime}\", \"{timestamp}\");"
        self.execute_sql(sql, self.cur)

    # 数据插入接口，Client的on_message统一调用该方法
    def dump_ws(self, data):
        """
        {
          "e": "24hrTicker",  // Event type
          "E": 123456789,     // Event time
          "s": "BNBBTC",      // Symbol
          "p": "0.0015",      // Price change
          "P": "250.00",      // Price change percent
          "w": "0.0018",      // Weighted average price
          "x": "0.0009",      // First trade(F)-1 price (first trade before the 24hr rolling window)
          "c": "0.0025",      // Last price
          "Q": "10",          // Last quantity
          "b": "0.0024",      // Best bid price
          "B": "10",          // Best bid quantity
          "a": "0.0026",      // Best ask price
          "A": "100",         // Best ask quantity
          "o": "0.0010",      // Open price
          "h": "0.0025",      // High price
          "l": "0.0010",      // Low price
          "v": "10000",       // Total traded base asset volume
          "q": "18",          // Total traded quote asset volume
          "O": 0,             // Statistics open time
          "C": 86400000,      // Statistics close time
          "F": 0,             // First trade ID
          "L": 18150,         // Last trade Id
          "n": 18151          // Total number of trades
        }
        以上结果是使用ws接口的返回，如果使用stream，返回格式为是{"stream": “24hrTicker”, "data":...}，需要先取一次data
        部分stream接口data的key会有所不同
        """
        # 返回时间戳单位为s
        timestamp = int(data["E"] * 1e-3)
        # 通过时间戳构造datetime
        datetime = time.strftime("%Y-%m-%d %H:%M:%S")
        symbol = data["s"]
        price = data["c"]
        self._insert(symbol, price, datetime, timestamp)

        # 测试:通过requests请求获取tickerPrice作为对比，保证获取到的数据是实时价格
        # print(symbol, price, datetime, timestamp)
        # resp = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}",
        #                     proxies=requests_proxies).json()
        # print(resp)

    def dump_http(self, data: list):
        """
        use a single INSERT with multiple VALUES will boost speed greatly
        其他提速方法可能可以采取采用2个以上insert语句，并使用aiomysql
        或者直接构造sql文件也可以
        目前来看还是请求占用时间较多
        """
        sql = f"INSERT INTO {table_info} (SYMBOL, PRICE, DATETIME, TIMESTAMP) VALUES "
        body = []
        for item in data:
            timestamp = item["TIMESTAMP"]
            datetime = item["DATETIME"]
            symbol = item["SYMBOL"]
            price = item["PRICE"]
            body.append(f"(\"{symbol}\", \"{price}\", \"{datetime}\", \"{timestamp}\")")
        sql = sql + ",".join(body) + ";"

        self.execute_sql(sql, self.cur)


if __name__ == "__main__":
    initor = Initor()
    initor.database_init()
