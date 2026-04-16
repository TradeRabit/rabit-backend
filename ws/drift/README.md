# Drift Protocol WebSocket Client

Real-time futures market data from Drift Protocol via WebSocket.

## 🚀 Quick Start

```python
import asyncio
from ws.drift import DriftWSClient

async def main():
    client = DriftWSClient()
    
    # Connect
    await client.connect()
    
    # Subscribe to SOL futures
    await client.subscribe("SOL", lambda p: print(f"${p.price}"))
    
    # Wait for updates
    await asyncio.sleep(30)
    
    # Cleanup
    await client.disconnect()

asyncio.run(main())
```

## 📊 Features

- ✅ Real-time futures price updates
- ✅ 24h change & volume
- ✅ Open Interest (OI)
- ✅ Funding Rate (1h)
- ✅ Up to 25 concurrent symbols
- ✅ Async callbacks
- ✅ Error handling

## 📈 Data Fields

```python
PriceUpdate(
    symbol="SOL",
    price=150.50,
    change_24h=2.5,        # Percentage
    volume_24h=1000000,
    open_interest=5000000,  # Unique to Drift
    funding_rate=0.01       # Unique to Drift
)
```

## ⚙️ Configuration

```python
# config/settings.py
DRIFT_WS_URL = "wss://drift-mainnet.rpc.drift.trade"
DRIFT_SUBSCRIBE_ASSETS = 25  # Max concurrent subscriptions
DRIFT_ASSETS = ["SOL", "BTC", "ETH", ...]
```

## 📚 Documentation

- [WebSocket Structure](../../docs/websocket/WS_STRUCTURE.md)
- [API Reference](../../docs/api/API_REFERENCE.md)

## 🧪 Testing

```bash
python test/test_drift.py
```

## 🔗 Resources

- [Drift Protocol](https://www.drift.trade/)
- [Drift Docs](https://docs.drift.trade/)

## 💡 Use Cases

### Price Monitoring
```python
await client.subscribe("SOL", lambda p: print(f"SOL: ${p.price}"))
```

### Funding Rate Alerts
```python
async def check_funding(price: PriceUpdate):
    if price.funding_rate and abs(price.funding_rate) > 0.05:
        print(f"⚠️ High funding rate: {price.funding_rate}%")

await client.subscribe("SOL", check_funding)
```

### Open Interest Tracking
```python
async def track_oi(price: PriceUpdate):
    if price.open_interest:
        print(f"OI: ${price.open_interest:,.0f}")

await client.subscribe("BTC", track_oi)
```

## 🆚 vs Backpack

| Feature | Drift | Backpack |
|---------|-------|----------|
| Open Interest | ✅ | ❌ |
| Funding Rate | ✅ | ❌ |
| High/Low 24h | ❌ | ✅ |
| Trade Stream | ❌ | ✅ |
| Max Symbols | 25 | Unlimited |
| Market Type | Futures | Spot |
