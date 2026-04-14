# WebSocket Module Structure

## 📁 Organized Folder Structure

```
ws/
├── __init__.py                 # Main module exports
├── drift/                      # Drift Protocol WebSocket
│   ├── __init__.py
│   └── client.py              # DriftWSClient
├── binance/                    # Binance OHLC data
│   ├── __init__.py
│   ├── client.py              # BinanceClient
│   └── history.py             # BinanceHistoryDownloader
├── models/                     # Data models
│   ├── __init__.py
│   └── market_data.py         # PriceUpdate, OHLCData, MarketData
└── handlers/                   # Event handlers
    ├── __init__.py
    └── market_handler.py      # MarketDataHandler
```

## 🎯 Module Organization by Feature

### 1. **Drift Module** (`ws/drift/`)
**Purpose**: Real-time market data from Drift Protocol

**Files**:
- `client.py` - DriftWSClient class

**Exports**:
```python
from ws.drift import DriftWSClient
```

**Features**:
- Subscribe to 25 assets (configurable)
- Real-time price updates
- 24h change, volume, open interest, funding rate
- Async callbacks for price updates

**Data Fields**:
- `price` - Current price
- `change_24h` - 24-hour price change
- `volume_24h` - 24-hour trading volume
- `open_interest` - Open interest
- `funding_rate` - Current funding rate (1h)

### 2. **Binance Module** (`ws/binance/`)
**Purpose**: OHLC data for charting (TradingView compatible)

**Files**:
- `client.py` - BinanceClient for real-time OHLC
- `history.py` - BinanceHistoryDownloader for historical data

**Exports**:
```python
from ws.binance import BinanceClient, BinanceHistoryDownloader
```

**Features**:
- Real-time OHLC data via WebSocket
- Historical OHLC data download
- Configurable intervals (1m, 5m, 15m, 1h, 4h, 1d)
- Batch download for multiple symbols

**OHLC Data**:
- `open` - Opening price
- `high` - Highest price
- `low` - Lowest price
- `close` - Closing price
- `volume` - Trading volume
- `quote_asset_volume` - Quote asset volume
- `number_of_trades` - Number of trades
- `taker_buy_base_asset_volume` - Taker buy base volume
- `taker_buy_quote_asset_volume` - Taker buy quote volume

### 3. **Models Module** (`ws/models/`)
**Purpose**: Data models for WebSocket data

**Files**:
- `market_data.py` - PriceUpdate, OHLCData, MarketData

**Exports**:
```python
from ws.models import MarketData, OHLCData, PriceUpdate
```

**Models**:
- `PriceUpdate` - Real-time price data from Drift
- `OHLCData` - OHLC candle data from Binance
- `MarketData` - Combined market data

### 4. **Handlers Module** (`ws/handlers/`)
**Purpose**: Event handling for market data

**Files**:
- `market_handler.py` - MarketDataHandler class

**Exports**:
```python
from ws.handlers import MarketDataHandler
```

**Features**:
- Subscribe/unsubscribe to events
- Store latest price and OHLC data
- Notify listeners on updates
- Get price/OHLC data by symbol

## 🔄 Import Patterns

### From Main Module
```python
from ws import (
    DriftWSClient,
    BinanceClient,
    BinanceHistoryDownloader,
    MarketData,
    OHLCData,
    PriceUpdate,
    MarketDataHandler
)
```

### From Submodules
```python
# Drift
from ws.drift import DriftWSClient

# Binance
from ws.binance import BinanceClient, BinanceHistoryDownloader

# Models
from ws.models import MarketData, OHLCData, PriceUpdate

# Handlers
from ws.handlers import MarketDataHandler
```

## 📊 Configuration

### Environment Variables

```env
# Drift WebSocket
DRIFT_WS_URL=wss://drift-mainnet.rpc.drift.trade
DRIFT_SUBSCRIBE_ASSETS=25
DRIFT_ASSETS=SOL,BTC,ETH,USDC,USDT,ORCA,COPE,SAMO,STEP,...

# Binance Configuration
BINANCE_API_URL=https://api.binance.com
BINANCE_WS_URL=wss://stream.binance.com:9443/ws
BINANCE_OHLC_INTERVAL=1h
BINANCE_OHLC_DOWNLOAD_LIMIT=100

# Data Configuration
WS_DATA_FIELDS=price,change_24h,volume_24h,open_interest,funding_rate
OHLC_ENABLED=true
OHLC_HISTORY_ENABLED=true
```

### Settings Access

```python
from config.settings import settings

# Drift settings
assets = settings.DRIFT_ASSETS
max_assets = settings.DRIFT_SUBSCRIBE_ASSETS

# Binance settings
interval = settings.BINANCE_OHLC_INTERVAL
limit = settings.BINANCE_OHLC_DOWNLOAD_LIMIT

# Data fields
fields = settings.WS_DATA_FIELDS
```

## 🚀 Usage Examples

### 1. Subscribe to Drift Price Updates

```python
from ws import DriftWSClient, MarketDataHandler

# Initialize
drift_client = DriftWSClient()
handler = MarketDataHandler()

# Connect
await drift_client.connect()

# Subscribe to price updates
async def on_price_update(price_update):
    print(f"{price_update.symbol}: {price_update.price}")

await drift_client.subscribe("SOL", handler.on_price_update)

# Disconnect
await drift_client.disconnect()
```

### 2. Subscribe to Binance OHLC

```python
from ws import BinanceClient, MarketDataHandler

# Initialize
binance_client = BinanceClient()
handler = MarketDataHandler()

# Connect
await binance_client.connect()

# Subscribe to OHLC
async def on_ohlc_update(ohlc_data):
    print(f"{ohlc_data.symbol}: {ohlc_data.close}")

await binance_client.subscribe_ohlc("SOLUSDT", handler.on_ohlc_update)

# Disconnect
await binance_client.disconnect()
```

### 3. Download Historical OHLC Data

```python
from ws import BinanceHistoryDownloader
from datetime import datetime, timedelta

# Initialize
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

# Download for multiple symbols
symbols = ["SOLUSDT", "BTCUSDT", "ETHUSDT"]
all_data = await downloader.download_multiple(symbols)
```

### 4. Use Market Data Handler

```python
from ws import MarketDataHandler

handler = MarketDataHandler()

# Subscribe to events
handler.subscribe("price:SOL", lambda price: print(f"Price: {price.price}"))
handler.subscribe("ohlc:SOLUSDT", lambda ohlc: print(f"Close: {ohlc.close}"))

# Get latest data
price = handler.get_price("SOL")
ohlc_list = handler.get_ohlc("SOLUSDT", limit=10)

# Get all data
all_prices = handler.get_all_prices()
all_ohlc = handler.get_all_ohlc()
```

## 📈 Data Flow

```
┌─────────────────────────────────────┐
│  Drift WebSocket                    │
│  (Real-time prices)                 │
└──────────────┬──────────────────────┘
               │
               ▼
        ┌──────────────┐
        │ DriftWSClient│
        └──────┬───────┘
               │
               ▼
        ┌──────────────────┐
        │ PriceUpdate      │
        │ - price          │
        │ - change_24h     │
        │ - volume_24h     │
        │ - open_interest  │
        │ - funding_rate   │
        └──────┬───────────┘
               │
               ▼
        ┌──────────────────┐
        │ MarketDataHandler│
        │ - on_price_update│
        │ - notify_listeners
        └──────────────────┘

┌─────────────────────────────────────┐
│  Binance WebSocket                  │
│  (Real-time OHLC)                   │
└──────────────┬──────────────────────┘
               │
               ▼
        ┌──────────────┐
        │ BinanceClient│
        └──────┬───────┘
               │
               ▼
        ┌──────────────────┐
        │ OHLCData         │
        │ - open, high, low│
        │ - close, volume  │
        │ - trades, etc    │
        └──────┬───────────┘
               │
               ▼
        ┌──────────────────┐
        │ MarketDataHandler│
        │ - on_ohlc_update │
        │ - notify_listeners
        └──────────────────┘

┌─────────────────────────────────────┐
│  Binance REST API                   │
│  (Historical OHLC)                  │
└──────────────┬──────────────────────┘
               │
               ▼
        ┌──────────────────────┐
        │ BinanceHistoryDownl. │
        │ - download_ohlc()    │
        │ - download_multiple()│
        └──────────────────────┘
```

## 🔧 Best Practices

1. **Asset Limit** - Max 25 assets for Drift (configurable)
2. **OHLC Storage** - Keep last 100 candles in memory
3. **Error Handling** - All errors logged, callbacks wrapped
4. **Async Callbacks** - Support both sync and async callbacks
5. **Connection Management** - Proper connect/disconnect handling
6. **Data Validation** - Pydantic models for type safety

## 📝 Adding New Data Source

### Step 1: Create Client Module
```
ws/new_source/
├── __init__.py
└── client.py
```

### Step 2: Implement Client
```python
class NewSourceClient:
    async def connect(self):
        pass
    
    async def subscribe(self, symbol, callback):
        pass
    
    async def disconnect(self):
        pass
```

### Step 3: Export in Main Module
```python
# ws/__init__.py
from ws.new_source import NewSourceClient
__all__ = [..., "NewSourceClient"]
```

---

**Last Updated**: 2026-04-14
**Version**: 1.0.0
