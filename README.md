# requirement

涉及库比较少，我也没搞新的环境，就没弄requirements.txt

- websocket-client==1.3.2  # 安装请认准websocket-client，调用时直接是websocket，类似库很多很容易弄错

- requests==2.27.1

- PyMySQL==1.0.2

# 关于BinanceAPI

官方文档：https://github.com/binance/binance-spot-api-docs/

官方文档2：https://binance-docs.github.io/apidocs/spot/en/#change-log

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

### 查询限制：

- WebSocket connections have a limit of 5 incoming messages per second. A message is considered:
  - A PING frame
  - A PONG frame
  - A JSON controlled message (e.g. subscribe, unsubscribe)
- A connection that goes beyond the limit will be disconnected; IPs that are repeatedly disconnected may be banned.
- A single connection can listen to a maximum of 1024 streams.

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
params：可以支持联合查询
	eg："params": ["BTCUSDT@ticker", "BNBBTC@ticker"]
"""
```

- 若订阅成功，会首先返回一个{result:"Null"}

- 目前使用不带参的ticker接口，会自动返回流动信息（只要价格发生变化就会推送，推送内容为详细信息），数据量大概在500-800条/秒左右。

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

### K线接口：

**Kline/Candlestick chart intervals:**

m -> minutes; h -> hours; d -> days; w -> weeks; M -> months

- 1m
- 3m
- 5m
- 15m
- 30m
- 1h
- 2h
- 4h
- 6h
- 8h
- 12h
- 1d
- 3d
- 1w
- 1M

**Stream Name:** <symbol>@kline_<interval>

**Update Speed:** 2000ms

**Payload:**

```
{
  "e": "kline",     // Event type
  "E": 123456789,   // Event time
  "s": "BNBBTC",    // Symbol
  "k": {
    "t": 123400000, // Kline start time
    "T": 123460000, // Kline close time
    "s": "BNBBTC",  // Symbol
    "i": "1m",      // Interval
    "f": 100,       // First trade ID
    "L": 200,       // Last trade ID
    "o": "0.0010",  // Open price
    "c": "0.0020",  // Close price
    "h": "0.0025",  // High price
    "l": "0.0015",  // Low price
    "v": "1000",    // Base asset volume
    "n": 100,       // Number of trades
    "x": false,     // Is this kline closed?
    "q": "1.0000",  // Quote asset volume
    "V": "500",     // Taker buy base asset volume
    "Q": "0.500",   // Taker buy quote asset volume
    "B": "123456"   // Ignore
  }
}
```

**attention：**

- 查询时请使用小写symbol
- 满足查询interval时，结束参数data\["k"]["x"]为True，统一都是取整分钟作为K线开始时间
- 币种更新会有延迟，和订阅币种数量关系不大，部分冷门币种接口数据更新很慢（比如ethtusd，一分钟只推送两次，且基本上要过8秒才会返回上一分钟的数据，这是binance服务器的原因）

## 其他

关于DATABASE

INFO

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

COIN

| COLUMN_NAME | COLUMN_TYPE | DATA_TYPE | CHARACTER_MAXIMUM_LENGTH | IS_NULLABLE |
| ----------- | ----------- | --------- | ------------------------ | ----------- |
| SYMBOL      | varchar(20) | varchar   | 20                       | NO          |

```mysql
CREATE TABLE `coin` (
  `SYMBOL` varchar(20) NOT NULL,
  PRIMARY KEY (`SYMBOL`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8；
```


