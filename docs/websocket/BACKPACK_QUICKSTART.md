# Backpack Exchange Quick Start Guide

## 🚀 Quick Start

### Installation

```bash
pip install bpx-py
```

### Basic Usage (5 minutes)

```python
import asyncio
from ws.backpack import BackpackWSClient
from ws.models import PriceUpdate

async def main():
    # Create client
    client = BackpackWSClient()
    
    # Define callback
    async def on_price(price: PriceUpdate):
        print(f"💰 {price.symbol}: ${price.price:.2f}")
        if price.change_24h:
            print(f"   📈 24h: {price.change_24h:+.2f}%")
    
    # Connect and subscribe
    await client.connect()
    await client.subscribe("SOL_USDC", on_price)
    
    # Wait for updates
    await asyncio.sleep(30)
    
    # Cleanup
    await client.disconnect()

# Run
asyncio.run(main())
```

## 📊 Available Symbols

Common trading pairs on Backpack:

```python
symbols = [
    "SOL_USDC",   # Solana
    "BTC_USDC",   # Bitcoin
    "ETH_USDC",   # Ethereum
    "USDT_USDC",  # Tether
    "BONK_USDC",  # Bonk
    "JUP_USDC",   # Jupiter
    "WIF_USDC",   # Dogwifhat
    "PYTH_USDC",  # Pyth Network
    "JTO_USDC",   # Jito
    "RNDR_USDC",  # Render
]
```

## 🎯 Common Use Cases

### 1. Price Monitoring

```python
async def monitor_price():
    client = BackpackWSClient()
    await client.connect()
    
    await client.subscribe("SOL_USDC", lambda p: 
        print(f"SOL: ${p.price:.2f}")
    )
    
    await asyncio.sleep(60)
    await client.disconnect()
```

### 2. Multiple Symbols

```python
async def monitor_multiple():
    client = BackpackWSClient()
    await client.connect()
    
    symbols = ["SOL_USDC", "BTC_USDC", "ETH_USDC"]
    
    for symbol in symbols:
        await client.subscribe(symbol, on_price_update)
    
    await asyncio.sleep(60)
    await client.disconnect()
```

### 3. Price Alerts

```python
async def price_alert():
    client = BackpackWSClient()
    await client.connect()
    
    async def check_price(price: PriceUpdate):
        if price.price > 200:
            print(f"🚨 ALERT: {price.symbol} above $200!")
        if price.change_24h and price.change_24h > 10:
            print(f"🚀 ALERT: {price.symbol} pumping +{price.change_24h}%!")
    
    await client.subscribe("SOL_USDC", check_price)
    await asyncio.sleep(3600)  # Monitor for 1 hour
    await client.disconnect()
```

### 4. With MarketDataHandler

```python
from ws.backpack import BackpackWSClient
from ws.handlers import MarketDataHandler

async def with_handler():
    client = BackpackWSClient()
    handler = MarketDataHandler()
    
    await client.connect()
    await client.subscribe("SOL_USDC", handler.on_price_update)
    
    await asyncio.sleep(10)
    
    # Get latest price
    price = handler.get_price("SOL")
    if price:
        print(f"Latest: ${price.price:.2f}")
    
    await client.disconnect()
```

## 🔧 Configuration

No configuration needed! Backpack client works out of the box.

Optional: Reuse Drift asset configuration:

```python
# config/settings.py
DRIFT_ASSETS = ["SOL", "BTC", "ETH", ...]
DRIFT_SUBSCRIBE_ASSETS = 25
```

## 🧪 Testing

Run the test suite:

```bash
python test/test_backpack.py
```

## 📚 Data Structure

### PriceUpdate Model

```python
class PriceUpdate:
    symbol: str              # "SOL"
    price: float             # 150.50
    change_24h: float        # 2.5 (%)
    volume_24h: float        # 1000000
    high_24h: float          # 155.00
    low_24h: float           # 148.00
    open_interest: None      # Not available
    funding_rate: None       # Not available
    timestamp: datetime
```

## 🆚 Drift vs Backpack

| Feature | Drift | Backpack |
|---------|-------|----------|
| Price | ✅ | ✅ |
| 24h Change | ✅ | ✅ |
| Volume | ✅ | ✅ |
| High/Low | ❌ | ✅ |
| Open Interest | ✅ | ❌ |
| Funding Rate | ✅ | ❌ |
| Trade Stream | ❌ | ✅ |

**Recommendation**: Use both for comprehensive data!

## 🔗 Next Steps

- [Full Documentation](./BACKPACK_INTEGRATION.md)
- [WebSocket Structure](./WS_STRUCTURE.md)
- [API Reference](./API_REFERENCE.md)

## 💡 Tips

1. **Symbol Format**: Always use `BASE_QUOTE` (e.g., `SOL_USDC`)
2. **Callbacks**: Keep them fast and non-blocking
3. **Error Handling**: Always wrap in try-except
4. **Cleanup**: Always disconnect when done

## ❓ Troubleshooting

### Connection Issues

```python
try:
    await client.connect()
except Exception as e:
    print(f"Connection failed: {e}")
    # Retry logic...
```

### No Data Received

- Check symbol format (must be `BASE_QUOTE`)
- Verify symbol exists on Backpack Exchange
- Check internet connection
- Wait longer (some symbols have low activity)

### Rate Limits

Backpack doesn't have hard limits, but be reasonable:
- Don't subscribe to 100+ symbols
- Use same limit as Drift (25 symbols)

## 🎓 Examples

See `test/test_backpack.py` for complete examples:
- Basic connection
- Single symbol subscription
- Multiple symbols subscription
- Error handling
- Cleanup

---

**Ready to start?** Run the test:

```bash
python test/test_backpack.py
```

🎉 Happy trading!
