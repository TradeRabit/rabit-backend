# OHLC Database Integration

Database untuk menyimpan historical OHLC (candlestick) data dari berbagai exchange dengan support untuk semua timeframe.

## Overview

OHLC Database menyimpan data candlestick secara permanen dalam format JSON, mendukung multiple exchanges (Binance, Backpack, Drift) dan **semua timeframe** yang umum digunakan.

## Supported Timeframes

### Minutes
- `1m` - 1 minute
- `3m` - 3 minutes
- `5m` - 5 minutes
- `15m` - 15 minutes
- `30m` - 30 minutes

### Hours
- `1h` - 1 hour
- `2h` - 2 hours
- `4h` - 4 hours
- `6h` - 6 hours
- `8h` - 8 hours
- `12h` - 12 hours

### Days
- `1d` - 1 day
- `3d` - 3 days

### Weeks
- `1w` - 1 week

### Months
- `1M` - 1 month

## Features

- **Multi-Exchange Support**: Simpan data dari Binance, Backpack, Drift dalam satu database
- **Multi-Interval Support**: Berbagai timeframe (1m, 5m, 15m, 1h, 4h, 1d)
- **Auto-Save**: Otomatis simpan data dari history downloader dan realtime WebSocket
- **Merge Capability**: Gabungkan data baru dengan existing data, hapus duplikat
- **Time Range Filtering**: Query data berdasarkan timestamp range
- **Storage Limit**: Maksimal 10,000 candles per symbol/exchange/interval

## Database Structure

```json
{
  "BTC": {
    "binance": {
      "1h": [OHLCData, ...],
      "4h": [OHLCData, ...],
      "1d": [OHLCData, ...]
    },
    "backpack": {
      "1h": [OHLCData, ...]
    },
    "drift": {
      "1h": [OHLCData, ...]
    }
  },
  "SOL": {
    "binance": {
      "1h": [OHLCData, ...]
    }
  }
}
```

## Usage

### Basic Operations

```python
from ws.database import get_ohlc_database
from ws.models import OHLCData

# Get database instance (singleton)
db = get_ohlc_database()

# Save candles
candles = [OHLCData(...), ...]
db.save_candles(
    symbol="BTC",
    exchange="binance",
    interval="1h",
    candles=candles,
    merge=True  # Merge with existing data
)

# Get candles
candles = db.get_candles(
    symbol="BTC",
    exchange="binance",
    interval="1h",
    limit=100  # Get last 100 candles
)

# Get latest candle
latest = db.get_latest_candle("BTC", "binance", "1h")

# Get available symbols
all_symbols = db.get_available_symbols()
binance_symbols = db.get_available_symbols("binance")

# Get available intervals
intervals = db.get_available_intervals("BTC", "binance")

# Get statistics
stats = db.get_stats()
print(f"Total candles: {stats['total_candles']}")
```

### Time Range Filtering

```python
from datetime import datetime, timedelta

# Get candles from last 24 hours
end_time = int(datetime.now().timestamp() * 1000)
start_time = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)

candles = db.get_candles(
    symbol="BTC",
    exchange="binance",
    interval="1h",
    start_time=start_time,
    end_time=end_time
)
```

### History Downloader with Auto-Save

```python
from ws.binance.history import BinanceHistoryDownloader

# Create downloader with auto-save enabled
downloader = BinanceHistoryDownloader(auto_save=True)

# Download and automatically save to database
candles = await downloader.download_ohlc("SOLUSDT", limit=100)

# Data is now in database
db = get_ohlc_database()
saved_candles = db.get_candles("SOL", "binance", "1h")
```

### Realtime WebSocket Auto-Save

```python
from ws.handlers.market_handler import MarketDataHandler
from ws.backpack.service import get_backpack_service

# Create handler with auto-save enabled
handler = MarketDataHandler(auto_save_ohlc=True)

# Start service (will auto-save OHLC updates)
service = get_backpack_service()
await service.start(handler)

# OHLC data from WebSocket is automatically saved to database
```

## API Reference

### OHLCDatabase

#### `__init__(db_path: str = "data/ohlc_history.json")`
Initialize database with custom path.

#### `save_candles(symbol, exchange, interval, candles, merge=True)`
Save OHLC candles to database.

**Parameters:**
- `symbol` (str): Trading symbol (e.g., 'BTC', 'SOL')
- `exchange` (str): Exchange name ('binance', 'backpack', 'drift')
- `interval` (str): Candle interval (e.g., '1m', '5m', '1h', '1d')
- `candles` (List[OHLCData]): List of OHLC data
- `merge` (bool): Merge with existing data and remove duplicates

#### `get_candles(symbol, exchange, interval, limit=None, start_time=None, end_time=None)`
Get OHLC candles from database.

**Parameters:**
- `symbol` (str): Trading symbol
- `exchange` (str): Exchange name
- `interval` (str): Candle interval
- `limit` (int, optional): Maximum number of candles (most recent)
- `start_time` (int, optional): Filter by start timestamp (milliseconds)
- `end_time` (int, optional): Filter by end timestamp (milliseconds)

**Returns:** List[OHLCData]

#### `get_latest_candle(symbol, exchange, interval)`
Get the most recent candle.

**Returns:** OHLCData or None

#### `get_available_symbols(exchange=None)`
Get list of available symbols, optionally filtered by exchange.

**Returns:** List[str]

#### `get_available_intervals(symbol, exchange)`
Get available intervals for a symbol/exchange.

**Returns:** List[str]

#### `delete_candles(symbol, exchange, interval)`
Delete candles for a specific symbol/exchange/interval.

#### `clear_exchange(exchange)`
Clear all data for a specific exchange.

#### `clear_all()`
Clear all OHLC data.

#### `get_stats()`
Get database statistics.

**Returns:** Dict with:
- `total_symbols`: Number of symbols
- `total_candles`: Total number of candles
- `exchanges`: Per-exchange statistics
- `database_path`: Path to database file
- `database_size_bytes`: File size in bytes

## Configuration

Database path can be configured:

```python
from ws.database import OHLCDatabase

# Custom path
db = OHLCDatabase(db_path="custom/path/ohlc.json")
```

Default path: `data/ohlc_history.json`

## Storage Limits

- **Max candles per interval**: 10,000
- Oldest candles are automatically removed when limit is reached
- Use `merge=True` to prevent duplicates

## Testing

Run the test suite:

```bash
python test/test_ohlc_database.py
```

Tests include:
- Basic CRUD operations
- Merge functionality
- Multi-exchange support
- Time range filtering
- Binance history download with auto-save

## File Location

- Database: `ws/database/ohlc_database.py`
- Models: `ws/models/market_data.py`
- Tests: `test/test_ohlc_database.py`

## Integration Points

1. **History Downloaders**
   - `ws/binance/history.py` - Auto-save on download
   - `ws/backpack/history.py` - Placeholder for future
   - `ws/drift/history.py` - Placeholder for future

2. **WebSocket Services**
   - `ws/backpack/service.py` - Auto-save realtime OHLC
   - `ws/drift/service.py` - Auto-save realtime OHLC

3. **Market Handler**
   - `ws/handlers/market_handler.py` - Coordinates auto-save

## Interval Utilities

```python
from ws.utils import (
    SUPPORTED_INTERVALS,
    get_interval_ms,
    get_interval_seconds,
    is_valid_interval,
    get_interval_category,
    get_intervals_by_category,
    format_interval_human
)

# Check all supported intervals
print(SUPPORTED_INTERVALS)
# ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']

# Get interval duration
ms = get_interval_ms("1h")  # 3600000
seconds = get_interval_seconds("1h")  # 3600

# Validate interval
is_valid = is_valid_interval("5m")  # True
is_valid = is_valid_interval("10m")  # False

# Get category
category = get_interval_category("4h")  # "hour"

# Get intervals by category
by_category = get_intervals_by_category()
# {
#   "minute": ["1m", "3m", "5m", "15m", "30m"],
#   "hour": ["1h", "2h", "4h", "6h", "8h", "12h"],
#   "day": ["1d", "3d"],
#   "week": ["1w"],
#   "month": ["1M"]
# }

# Human-readable format
human = format_interval_human("4h")  # "4 hours"
```

## Notes

- Database uses JSON format for easy inspection and portability
- All timestamps are in milliseconds (Unix epoch)
- Symbol names are normalized (uppercase, base asset only)
- Exchange names are normalized (lowercase)
- Data persists across server restarts
