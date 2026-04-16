# Binance WebSocket & REST Client

OHLC (candlestick) data for charting from Binance via WebSocket and REST API.

## 🚀 Quick Start

### Real-time OHLC (WebSocket)

```python
import asyncio
from ws.binance import BinanceClient

async def main():
    client = BinanceClient()
    
    # Connect
    await client.connect()
    
    # Subscribe to OHLC
    await client.subscribe_ohlc("SOLUSDT", lambda ohlc: 
        print(f"Close: ${ohlc.close}")
    )
    
    # Wait for updates
    await asyncio.sleep(30)
    
    # Cleanup
    await client.disconnect()

asyncio.run(main())
```

### Historical OHLC (REST API)

```python
from ws.binance import BinanceHistoryDownloader
from datetime import datetime, timedelta

async def main():
    downloader = BinanceHistoryDownloader()
    
    # Download last 100 candles
    ohlc_data = await downloader.download_ohlc("SOLUSDT")
    
    # Download for date range
    start = datetime.now() - timedelta(days=7)
    end = datetime.now()
    ohlc_data = await downloader.download_ohlc(
        "SOLUSDT",
        start_time=start,
        end_time=end
    )
    
    # Download multiple symbols
    symbols = ["SOLUSDT", "BTCUSDT", "ETHUSDT"]
    all_data = await downloader.download_multiple(symbols)

asyncio.run(main())
```

## 📊 Features

### BinanceClient (WebSocket)
- ✅ Real-time OHLC updates
- ✅ Configurable intervals (1m, 5m, 15m, 1h, 4h, 1d)
- ✅ Multiple symbol support
- ✅ Async callbacks

### BinanceHistoryDownloader (REST)
- ✅ Historical OHLC data
- ✅ Date range queries
- ✅ Batch downloads
- ✅ Configurable limit

## 📈 OHLC Data Structure

```python
OHLCData(
    symbol="SOLUSDT",
    timestamp=1614550000000,  # Unix timestamp (ms)
    open=150.00,
    high=155.00,
    low=148.00,
    close=152.50,
    volume=1000000,
    quote_asset_volume=152500000,
    number_of_trades=5000,
    taker_buy_base_asset_volume=600000,
    taker_buy_quote_asset_volume=91500000
)
```

## ⚙️ Configuration

```python
# config/settings.py
BINANCE_API_URL = "https://api.binance.com"
BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"
BINANCE_OHLC_INTERVAL = "1h"  # 1m, 5m, 15m, 1h, 4h, 1d
BINANCE_OHLC_DOWNLOAD_LIMIT = 100
```

## 📚 Documentation

- [WebSocket Structure](../../docs/websocket/WS_STRUCTURE.md)
- [API Reference](../../docs/api/API_REFERENCE.md)

## 🧪 Testing

```bash
python test/test_binance.py
```

## 🔗 Resources

- [Binance API Docs](https://binance-docs.github.io/apidocs/)
- [WebSocket Streams](https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams)

## 💡 Use Cases

### TradingView Integration
```python
# Get OHLC data for charting
ohlc_list = handler.get_ohlc("SOLUSDT", limit=100)

# Format for TradingView
candles = [{
    "time": ohlc.timestamp,
    "open": ohlc.open,
    "high": ohlc.high,
    "low": ohlc.low,
    "close": ohlc.close,
    "volume": ohlc.volume
} for ohlc in ohlc_list]
```

### Technical Analysis
```python
async def analyze_candle(ohlc: OHLCData):
    # Calculate indicators
    body = abs(ohlc.close - ohlc.open)
    range_size = ohlc.high - ohlc.low
    
    if body / range_size > 0.7:
        print("Strong momentum candle")
```

### Historical Backtesting
```python
# Download 1 year of data
start = datetime.now() - timedelta(days=365)
end = datetime.now()

ohlc_data = await downloader.download_ohlc(
    "BTCUSDT",
    start_time=start,
    end_time=end,
    interval="1d"
)

# Run backtest strategy
for candle in ohlc_data:
    # Your strategy logic...
    pass
```

## 🎯 Intervals

Available intervals:
- `1m` - 1 minute
- `5m` - 5 minutes
- `15m` - 15 minutes
- `1h` - 1 hour
- `4h` - 4 hours
- `1d` - 1 day

## 📊 Symbol Format

Binance uses format: `BASEQUOTE` (no separator)
- ✅ `SOLUSDT` - SOL/USDT
- ✅ `BTCUSDT` - BTC/USDT
- ✅ `ETHUSDT` - ETH/USDT
- ✅ `BNBUSDT` - BNB/USDT

## 🔄 Data Flow

```
Binance WS → BinanceClient → OHLCData → MarketDataHandler → Subscribers
Binance API → BinanceHistoryDownloader → OHLCData[] → Your App
```

## 🆚 WebSocket vs REST

| Feature | WebSocket | REST API |
|---------|-----------|----------|
| Real-time | ✅ | ❌ |
| Historical | ❌ | ✅ |
| Date Range | ❌ | ✅ |
| Continuous | ✅ | ❌ |
| Rate Limit | Low | Higher |
| Use Case | Live charts | Backtesting |
