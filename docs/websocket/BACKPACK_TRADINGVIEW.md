# Backpack Integration for TradingView Advanced Chart

## Overview

Backpack Exchange WebSocket client is now fully integrated with TradingView Advanced Chart support, providing real-time price updates and OHLC (candlestick) data.

## Features

### ✅ Implemented

1. **Real-time Price Updates**
   - Ticker stream: 24h statistics (price, volume, high, low, change%)
   - Trade stream: Real-time trade prices
   - Automatic symbol normalization (SOL_USDC → SOL)

2. **OHLC/Kline Data**
   - Multiple timeframes: 1m, 5m, 15m, 1h, 4h, 1d
   - Real-time candlestick updates
   - Compatible with TradingView chart format

3. **Market Data Handler Integration**
   - Unified handler for all price sources
   - Callback system for price and OHLC updates
   - Support for multiple intervals per symbol

4. **API Endpoints**
   - `/api/assets` - List assets with prices
   - `/api/assets/{symbol}` - Detailed asset info
   - `/api/assets/{symbol}/ohlc` - OHLC data with source selection
   - `/api/ws/prices` - WebSocket for real-time updates

## Configuration

### Environment Variables

```bash
# Backpack Exchange
BACKPACK_WS_URL=wss://ws.backpack.exchange
BACKPACK_ENABLED=true
BACKPACK_QUOTE_ASSET=USDC

# Price Source Selection
PRICE_SOURCE=backpack  # or "drift"
```

### Symbol Format

Backpack uses `BASE_QUOTE` format (e.g., `SOL_USDC`, `BTC_USDC`), which is automatically converted to base symbol (e.g., `SOL`, `BTC`) for API responses.

## Architecture

### WebSocket Client (`ws/backpack/client.py`)

```python
class BackpackWSClient:
    - connect() / disconnect()
    - subscribe(symbol, callback, subscribe_ohlc=True)
    - subscribe_ohlc(symbol, callback)
    - _handle_ticker() - 24h statistics
    - _handle_trade() - Real-time trades
    - _handle_kline() - OHLC candlestick data
```

### Service Layer (`ws/backpack/service.py`)

```python
class BackpackService:
    - start(handler) - Initialize and subscribe to assets
    - stop() - Clean shutdown
    - is_running() - Connection status
    - get_subscribed_symbols() - List subscriptions
```

### Market Data Handler (`ws/handlers/market_handler.py`)

```python
class MarketDataHandler:
    - on_price_update(price_update) - Handle price updates
    - on_ohlc_update(ohlc_data) - Handle OHLC updates
    - get_price(symbol) - Get latest price
    - get_ohlc(symbol, interval, limit) - Get OHLC data
```

## Usage

### Starting the Service

The service starts automatically in `main.py` based on `PRICE_SOURCE` setting:

```python
# In main.py lifespan
if settings.PRICE_SOURCE == "backpack":
    from ws.backpack import get_backpack_service
    backpack_service = get_backpack_service()
    await backpack_service.start(market_handler)
```

### API Usage

#### Get OHLC Data

```bash
# Auto-select source based on PRICE_SOURCE
GET /api/assets/SOL/ohlc?interval=1h&limit=100

# Force specific source
GET /api/assets/SOL/ohlc?interval=1h&limit=100&source=backpack
GET /api/assets/SOL/ohlc?interval=1h&limit=100&source=binance
```

Response:
```json
{
  "symbol": "SOL",
  "interval": "1h",
  "data": [
    {
      "timestamp": 1234567890000,
      "open": 150.00,
      "high": 155.00,
      "low": 148.00,
      "close": 152.00,
      "volume": 10000.0
    }
  ]
}
```

#### WebSocket Real-time Updates

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/prices');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
  // {
  //   "symbol": "SOL",
  //   "price": 152.50,
  //   "change_24h": 2.5,
  //   "volume_24h": 1000000,
  //   "timestamp": "2024-01-01T00:00:00Z"
  // }
};
```

## Data Flow

```
Backpack WebSocket
    ↓
BackpackWSClient
    ↓ (callbacks)
MarketDataHandler
    ↓
API Endpoints / WebSocket Broadcast
    ↓
TradingView Chart / Mobile App
```

## Comparison: Backpack vs Drift

| Feature | Backpack | Drift |
|---------|----------|-------|
| Real-time Price | ✅ Ticker + Trade | ✅ Market Data |
| OHLC/Kline | ✅ 6 intervals | ❌ Not available |
| 24h Statistics | ✅ High/Low/Volume | ✅ Change/Volume |
| Futures Data | ❌ Spot only | ✅ OI + Funding |
| Symbol Format | BASE_QUOTE | BASE |
| Update Frequency | High (trade-level) | Medium |

## TradingView Integration

### Supported Intervals

- `1m` - 1 minute
- `5m` - 5 minutes
- `15m` - 15 minutes
- `1h` - 1 hour
- `4h` - 4 hours
- `1d` - 1 day

### Data Format

OHLC data follows TradingView format:
```typescript
interface OHLCData {
  timestamp: number;  // Unix timestamp in milliseconds
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}
```

## Fallback Strategy

If Backpack real-time data is insufficient, the API automatically falls back to Binance historical data:

```python
# In api/routes.py
ohlc_data = market_handler.get_ohlc(symbol, interval, limit)

if len(ohlc_data) < limit:
    # Fallback to Binance
    ohlc_data = await binance_downloader.download_history(...)
```

## Testing

### Test WebSocket Connection

```python
# test/test_backpack.py
async def test_backpack_connection():
    client = BackpackWSClient()
    await client.connect()
    assert client.connected
```

### Test OHLC Subscription

```python
async def test_ohlc_subscription():
    client = BackpackWSClient()
    await client.connect()
    
    received_data = []
    
    async def callback(ohlc):
        received_data.append(ohlc)
    
    await client.subscribe("SOL", callback, subscribe_ohlc=True)
    client.subscribe_ohlc("SOL", callback)
    
    await asyncio.sleep(5)
    assert len(received_data) > 0
```

## Monitoring

### Check Service Status

```python
from ws.backpack import get_backpack_service

service = get_backpack_service()
print(f"Running: {service.is_running()}")
print(f"Subscribed: {service.get_subscribed_symbols()}")
```

### Logs

```
INFO - Starting Backpack WebSocket service...
INFO - Connected to Backpack WebSocket
INFO - Subscribed to SOL_USDC
INFO - Subscribed to BTC_USDC
INFO - Backpack service started, subscribed to 25 assets
```

## Troubleshooting

### No OHLC Data

1. Check if `BACKPACK_ENABLED=true`
2. Verify `PRICE_SOURCE=backpack`
3. Check logs for subscription errors
4. Ensure symbol is in `TRADING_ASSETS`

### Connection Issues

1. Check WebSocket URL: `wss://ws.backpack.exchange`
2. Verify network connectivity
3. Check rate limits (add delays between subscriptions)

### Symbol Not Found

1. Ensure symbol exists on Backpack
2. Check quote asset (default: USDC)
3. Verify symbol format (use base symbol in API, e.g., "SOL" not "SOL_USDC")

## Next Steps

1. ✅ Real-time price updates
2. ✅ OHLC/Kline data
3. ✅ TradingView integration
4. ✅ API endpoints
5. 🔄 Historical data from Backpack REST API (optional)
6. 🔄 Depth/orderbook data (optional)
7. 🔄 Advanced chart indicators (optional)

## References

- [Backpack WebSocket Documentation](https://docs.backpack.exchange/)
- [TradingView Charting Library](https://www.tradingview.com/charting-library-docs/)
- [Project Architecture](../architecture/ARCHITECTURE.md)
