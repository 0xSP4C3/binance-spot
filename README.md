# requirement

涉及库比较少，我也没搞新的环境，就没弄requirements.txt

- websocket-client==1.3.2  # 安装请认准websocket-client，调用时直接是websocket，类似库很多很容易弄错

- requests==2.27.1

- PyMySQL==1.0.2

# 关于BinanceAPI

官方文档：https://github.com/binance/binance-spot-api-docs/

官方python库：https://github.com/binance/binance-connector-python

- binance的所有api支持两种查询方式：http和websoket。官方库中，若使用Spot则是采用htt协议，查询方式类似于使用requests发送请求；若使用BinanceWebsoketClient则是使用websocket，主要实现订阅功能。我这里统一没有使用官方库。

## 使用requests访问

### 统一接口：

- https://api.binance.com/api/v3/

### 查询方式：

- 第一种是构造querystring，适用于所有请求

eg：https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT

- 第二种是使用requests带参，GET请求带进params里，POST请求代入data里

eg：略

- 不需要headers
- 返回格式为json
- 需要proxy

### 接口权重：

​	所有的接口都有对应权重，查询消耗权重，具体权重消耗/权重耗尽等问题请参考官方文档

## 使用websocket访问

### 统一接口：

- wss://dstream.binance.com/stream
- wss://stream.binance.com:9443/ws
- wss://stream.binance.com:9443/stream

### 查询方式：

- 建立连接后发送如下格式参数

```python
import json

data = {
            "method": "SUBSCRIBE",
            "id": 1,
            "params": ["!ticker"]
        }
ws.send(json.dumps(data))
    
"""
method：SUBSCRIBE表示订阅，UNSUBSCRIBE表示取消订阅，还有多种参数参见官方文档
id：用于区分返回的消息属于哪个订阅，自己设置
params：如果使用stream接口，可以支持联合查询
	eg："params": ["BTCUSDT@ticker", "BNBBTC@ticker"]
"""
```

- 若订阅成功，会首先返回一个{result:"Null"}

- 目前使用不带参的ticker接口，会自动返回流动信息（只要价格发生变化就会推送，推送内容为详细信息），数据量大概在500-800条/秒左右，能完全导入到数据库中。由于该订阅全名叫24hr_ticker，**不确定是否超过24h后需要重新订阅**。

- 每三分钟会发送一个Ping

- ticker接口返回的是详细信息，也可以采用miniTicker

```
{
    "stream": "24hrTicker",
    "data":
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
}
// 若使用ws接口，返回参数会略有不同
```

# 关于DATABASE

**以下是我自己用来存到本地Mysql时用的表结构**

## INFO

| COLUMN_NAME | COLUMN_TYPE  | DATA_TYPE | CHARACTER_MAXIMUM_LENGTH | IS_NULLABLE |
| ----------- | ------------ | --------- | ------------------------ | ----------- |
| ID          | int          | int       |                          | NO          |
| SYMBOL      | varchar(20)  | varchar   | 20                       | NO          |
| PRICE       | double(15,5) | double    |                          | YES         |
| DATETIME    | datetime     | datetime  |                          | NO          |
| TIMESTAMP   | bigint       | bigint    |                          | NO          |

除此之外在SYMBOL上有FOREIGN KEY和SIMPLE INDEX

**索引选的是最简单的SIMPLE INDEX，这方面不太了解**

```mysql
CREATE TABLE `info` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `SYMBOL` varchar(20) NOT NULL,
  `PRICE` double(15,5) DEFAULT NULL,
  `DATETIME` datetime NOT NULL,  
    # 若binance的API提供则使用提供的timestamp，不提供就写查询（发送请求）时间。为了保证数据精确，不适用录入数据库的时间
  `TIMESTAMP` bigint NOT NULL, 
  PRIMARY KEY (`ID`),
  KEY `SYMBOL` (`SYMBOL`),
  CONSTRAINT `FK_SYMBOL_COIN` FOREIGN KEY (`SYMBOL`) REFERENCES `coin` (`SYMBOL`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8；
```

## COIN

| COLUMN_NAME | COLUMN_TYPE | DATA_TYPE | CHARACTER_MAXIMUM_LENGTH | IS_NULLABLE |
| ----------- | ----------- | --------- | ------------------------ | ----------- |
| SYMBOL      | varchar(20) | varchar   | 20                       | NO          |

```mysql
CREATE TABLE `coin` (
  `SYMBOL` varchar(20) NOT NULL,
  PRIMARY KEY (`SYMBOL`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8；
```


