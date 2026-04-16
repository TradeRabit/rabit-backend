# Backpack Exchange WebSocket Client

Real-time market data from Backpack Exchange via WebSocket.

## 🚀 Quick Start

```python
import asyncio
from ws.backpack import BackpackWSClient

async def main():
    client = BackpackWSClient()
    
    # Connect
    await client.connect()
    
    # Subscribe
    await client.subscribe("SOL_USDC", lambda p: print(f"${p.price}"))
    
    # Wait for updates
    await asyncio.sleep(30)
    
    # Cleanup
    await client.disconnect()

asyncio.run(main())
```

## 📊 Features

- ✅ Real-time price updates
- ✅ 24h statistics (change, volume, high, low)
- ✅ Trade stream
- ✅ Multiple symbol support
- ✅ Async callbacks
- ✅ Error handling

## 📚 Documentation

- [Integration Guide](../../docs/BACKPACK_INTEGRATION.md)
- [Quick Start](../../docs/BACKPACK_QUICKSTART.md)
- [WebSocket Structure](../../docs/WS_STRUCTURE.md)

## 🧪 Testing

```bash
python test/test_backpack.py
```

## 🔗 Resources

- [Backpack API Docs](https://docs.backpack.exchange/)
- [bpx-py SDK](https://github.com/sndmndss/bpx-py)
