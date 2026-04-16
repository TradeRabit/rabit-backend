# Backpack Exchange WebSocket Integration

## 📋 Overview

Backpack Exchange WebSocket client untuk real-time market data. Menggunakan arsitektur yang sama dengan Drift client untuk konsistensi.

## 🔗 Resources

- **SDK**: [bpx-py](https://github.com/sndmndss/bpx-py) - `pip install bpx-py`
- **Documentation**: [Backpack API Docs](https://docs.backpack.exchange/)
- **WebSocket Guide**: [Python WebSocket Guide](https://support.backpack.exchange/exchange/api-and-developer-docs/python-websocket-guide-for-backpack-exchange-api)

## 🏗️ Architecture

```
ws/backpack/
├── __init__.py
└── client.py          # BackpackWSClient
```

## 📊 Features

### Real-time Data Streams

1. **Ticker Stream** (`ticker.<symbol>`)
   - Current price (lastPrice)
   - 24h price change (priceChange, priceChangePercent)
   - 24h volume
   - 24h high/low
   - Best bid/ask

2. **Trade Stream** (`trade.<symbol>`)
   - Recent trades
   - Trade price
   - Trade quantity
   - Trade side (buy/sell)
   - Trade timestamp

### Supported Symbols

Backpack uses format: `BASE_QUOTE` (e.g., `SOL_USDC`, `BTC_USDC`)

Common trading pairs:
- `SOL_USDC` - Solana
- `BTC_USDC` - Bitcoin
- `ETH_USDC` - Ethereum
- `USDT_USDC` - Tether
- `BONK_USDC` - Bonk
- `JUP_USDC` - Jupiter
- `WIF_USDC` - Dogwifhat

## 🚀 Usage

### Basic Connection

```python
from ws.backpack import BackpackWSClient

# Initialize client
client = BackpackWSClient()

# Connect
await client.connect()

# Disconnect
await client.disconnect()
```

### Subscribe to Market Data

```python
from ws.backpack import BackpackWSClient
from ws.models import PriceUpdate

async def on_price_update(price_update: PriceUpdate):
    print(f"{price_update.symbol}: ${price_update.price}")
    print(f"24h Change: {price_update.change_24h}%")
    print(f"24h Volume: ${price_update.volume_24h}")

# Initialize and connect
client = BackpackWSClient()
await client.connect()

# Subscribe to SOL_USDC
await client.subscribe("SOL_USDC", on_price_update)

# Wait for updates...
await asyncio.sleep(30)

# Unsubscribe
await client.unsubscribe("SOL_USDC")
await client.disconnect()
```

### Multiple Symbols

```python
# Subscribe to multiple symbols
symbols = ["SOL_USDC", "BTC_USDC", "ETH_USDC"]

for symbol in symbols:
    await client.subscribe(symbol, on_price_update)

# Check subscriptions
subscribed = client.get_subscribed_symbols()
print(f"Subscribed to: {subscribed}")

# Check specific symbol
is_subscribed = client.is_subscribed("SOL_USDC")
```

### Using with MarketDataHandler

```python
from ws.backpack import BackpackWSClient
from ws.handlers import MarketDataHandler

# Initialize
client = BackpackWSClient()
handler = MarketDataHandler()

# Connect
await client.connect()

# Subscribe using handler
await client.subscribe("SOL_USDC", handler.on_price_update)

# Get latest price
price = handler.get_price("SOL")
print(f"Latest SOL price: ${price.price}")
```

## 📡 WebSocket Protocol

### Connection

```
WebSocket URL: wss://ws.backpack.exchange
```

### Subscribe Message

```json
{
  "method": "SUBSCRIBE",
  "params": ["ticker.SOL_USDC", "trade.SOL_USDC"]
}
```

### Unsubscribe Message

```json
{
  "method": "UNSUBSCRIBE",
  "params": ["ticker.SOL_USDC"]
}
```

### Ticker Data Format

```json
{
  "stream": "ticker.SOL_USDC",
  "data": {
    "symbol": "SOL_USDC",
    "lastPrice": "150.50",
    "priceChange": "2.50",
    "priceChangePercent": "1.69",
    "volume": "1000000",
    "high": "155.00",
    "low": "148.00",
    "bidPrice": "150.45",
    "askPrice": "150.55"
  }
}
```

### Trade Data Format

```json
{
  "stream": "trade.SOL_USDC",
  "data": {
    "symbol": "SOL_USDC",
    "price": "150.50",
    "quantity": "10.5",
    "timestamp": 1614550000000,
    "side": "Buy"
  }
}
```

## 🔄 Data Mapping

Backpack data → PriceUpdate model:

| Backpack Field | PriceUpdate Field | Description |
|----------------|-------------------|-------------|
| `lastPrice` | `price` | Current price |
| `priceChangePercent` | `change_24h` | 24h change % |
| `volume` | `volume_24h` | 24h volume |
| `high` | `high_24h` | 24h high |
| `low` | `low_24h` | 24h low |
| N/A | `open_interest` | Not available |
| N/A | `funding_rate` | Not available |

**Note**: Backpack doesn't provide Open Interest or Funding Rate in public streams. These fields will be `None`.

## 🧪 Testing

Run the test suite:

```bash
python test/test_backpack.py
```

Tests include:
1. Basic connection test
2. Single symbol subscription
3. Multiple symbols subscription

## 🔧 Configuration

Backpack client reuses existing configuration from `config/settings.py`:

```python
# Reuses Drift asset list
DRIFT_ASSETS = ["SOL", "BTC", "ETH", ...]
DRIFT_SUBSCRIBE_ASSETS = 25  # Max concurrent subscriptions
```

## 📈 Comparison with Drift

| Feature | Drift | Backpack |
|---------|-------|----------|
| **Protocol** | Custom WS | Standard WS |
| **Price Data** | ✅ | ✅ |
| **24h Change** | ✅ | ✅ |
| **Volume** | ✅ | ✅ |
| **Open Interest** | ✅ | ❌ |
| **Funding Rate** | ✅ | ❌ |
| **High/Low 24h** | ❌ | ✅ |
| **Trade Stream** | ❌ | ✅ |
| **Max Symbols** | 25 | Unlimited* |

*Subject to Backpack's rate limits

## 🎯 Use Cases

### 1. Price Monitoring

```python
# Monitor SOL price in real-time
await client.subscribe("SOL_USDC", lambda p: print(f"SOL: ${p.price}"))
```

### 2. Multi-Exchange Comparison

```python
# Compare prices from Drift and Backpack
drift_client = DriftWSClient()
backpack_client = BackpackWSClient()

await drift_client.connect()
await backpack_client.connect()

await drift_client.subscribe("SOL", on_drift_update)
await backpack_client.subscribe("SOL_USDC", on_backpack_update)
```

### 3. Trading Bot Integration

```python
# Use Backpack data for trading decisions
async def on_price_update(price_update: PriceUpdate):
    if price_update.change_24h > 5.0:
        print(f"🚀 {price_update.symbol} pumping! +{price_update.change_24h}%")
        # Execute trading logic...
    elif price_update.change_24h < -5.0:
        print(f"📉 {price_update.symbol} dumping! {price_update.change_24h}%")
        # Execute trading logic...
```

## 🐛 Error Handling

The client includes comprehensive error handling:

```python
try:
    await client.connect()
    await client.subscribe("SOL_USDC", callback)
except websockets.exceptions.ConnectionClosed:
    print("Connection closed, reconnecting...")
    await client.connect()
except Exception as e:
    print(f"Error: {e}")
    await client.disconnect()
```

## 📝 Best Practices

1. **Connection Management**
   - Always disconnect when done
   - Handle connection errors gracefully
   - Implement reconnection logic for production

2. **Subscription Limits**
   - Backpack doesn't have hard limits, but be reasonable
   - Use same limit as Drift (25 symbols) for consistency

3. **Callback Performance**
   - Keep callbacks fast and non-blocking
   - Use async callbacks for I/O operations
   - Handle exceptions in callbacks

4. **Symbol Format**
   - Always use `BASE_QUOTE` format (e.g., `SOL_USDC`)
   - Check available symbols on Backpack Exchange

## 🔮 Future Enhancements

Potential improvements:

1. **Private Streams**
   - Account updates
   - Order updates
   - Balance updates
   - Requires API key authentication

2. **Order Book Stream**
   - Real-time depth updates
   - Full order book snapshots

3. **Historical Data**
   - OHLC data (similar to Binance integration)
   - Historical trades

4. **Advanced Features**
   - Automatic reconnection
   - Connection health monitoring
   - Rate limit handling

## 📚 Related Documentation

- [WS Structure](./WS_STRUCTURE.md) - Overall WebSocket architecture
- [Drift Integration](./OPENROUTER_INTEGRATION.md) - Drift client reference
- [Market Data Models](./WS_STRUCTURE.md#models-module) - Data models

---

**Last Updated**: 2026-04-16  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
