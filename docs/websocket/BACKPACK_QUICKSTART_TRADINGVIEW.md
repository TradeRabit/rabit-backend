# Backpack + TradingView Quick Start Guide

## 🚀 Quick Setup

### 1. Configure Environment

```bash
# .env
PRICE_SOURCE=backpack
BACKPACK_ENABLED=true
BACKPACK_WS_URL=wss://ws.backpack.exchange
BACKPACK_QUOTE_ASSET=USDC
```

### 2. Start the Server

```bash
python main.py
```

Expected output:
```
INFO - Starting Rabit Backend...
INFO - Price source: backpack
INFO - Starting Backpack WebSocket service...
INFO - Connected to Backpack WebSocket
INFO - Subscribed to SOL_USDC
INFO - Subscribed to BTC_USDC
INFO - Backpack service started, subscribed to 25 assets
INFO - Rabit Backend started successfully!
```

### 3. Test API Endpoints

#### Get Asset List
```bash
curl http://localhost:8000/api/assets
```

Response:
```json
{
  "assets": [
    {
      "symbol": "SOL",
      "name": "Solana",
      "price": 152.50,
      "change_24h": 2.5,
      "categories": ["Layer 1"]
    }
  ],
  "total": 25
}
```

#### Get OHLC Data for TradingView
```bash
curl "http://localhost:8000/api/assets/SOL/ohlc?interval=1h&limit=100"
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

ws.onopen = () => {
  console.log('Connected to price feed');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`${data.symbol}: $${data.price}`);
};
```

## 📊 TradingView Integration

### Using with TradingView Advanced Chart

```javascript
// TradingView Datafeed Configuration
const datafeed = {
  onReady: (callback) => {
    callback({
      supported_resolutions: ['1', '5', '15', '60', '240', '1D'],
      supports_marks: false,
      supports_timescale_marks: false,
    });
  },
  
  resolveSymbol: (symbolName, onResolve, onError) => {
    const symbolInfo = {
      name: symbolName,
      ticker: symbolName,
      description: symbolName,
      type: 'crypto',
      session: '24x7',
      timezone: 'Etc/UTC',
      minmov: 1,
      pricescale: 100,
      has_intraday: true,
      supported_resolutions: ['1', '5', '15', '60', '240', '1D'],
    };
    onResolve(symbolInfo);
  },
  
  getBars: async (symbolInfo, resolution, periodParams, onResult, onError) => {
    try {
      // Map TradingView resolution to API interval
      const intervalMap = {
        '1': '1m',
        '5': '5m',
        '15': '15m',
        '60': '1h',
        '240': '4h',
        '1D': '1d',
      };
      
      const interval = intervalMap[resolution] || '1h';
      const response = await fetch(
        `http://localhost:8000/api/assets/${symbolInfo.name}/ohlc?interval=${interval}&limit=1000`
      );
      
      const data = await response.json();
      
      const bars = data.data.map(candle => ({
        time: candle.timestamp,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
        volume: candle.volume,
      }));
      
      onResult(bars, { noData: bars.length === 0 });
    } catch (error) {
      onError(error);
    }
  },
  
  subscribeBars: (symbolInfo, resolution, onTick, listenerGuid, onResetCacheNeededCallback) => {
    // Connect to WebSocket for real-time updates
    const ws = new WebSocket('ws://localhost:8000/api/ws/prices');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.symbol === symbolInfo.name) {
        onTick({
          time: new Date(data.timestamp).getTime(),
          close: data.price,
        });
      }
    };
  },
};

// Initialize TradingView Widget
const widget = new TradingView.widget({
  container_id: 'tv_chart_container',
  datafeed: datafeed,
  symbol: 'SOL',
  interval: '60',
  library_path: '/charting_library/',
  locale: 'en',
  theme: 'dark',
});
```

## 🧪 Testing

### Test Backpack Connection
```bash
python test/test_backpack.py
```

### Test OHLC Subscription
```python
import asyncio
from test.test_backpack import test_backpack_ohlc

asyncio.run(test_backpack_ohlc())
```

### Test Service Integration
```python
import asyncio
from test.test_backpack import test_backpack_service

asyncio.run(test_backpack_service())
```

## 🔄 Switching Between Sources

### Use Backpack (Real-time + OHLC)
```bash
PRICE_SOURCE=backpack
BACKPACK_ENABLED=true
```

### Use Drift (Futures data)
```bash
PRICE_SOURCE=drift
```

### Hybrid: Backpack prices + Binance OHLC
```bash
PRICE_SOURCE=backpack
# In API call:
GET /api/assets/SOL/ohlc?source=binance
```

## 📈 Supported Intervals

| Interval | Description | Backpack | Binance |
|----------|-------------|----------|---------|
| 1m | 1 minute | ✅ | ✅ |
| 5m | 5 minutes | ✅ | ✅ |
| 15m | 15 minutes | ✅ | ✅ |
| 1h | 1 hour | ✅ | ✅ |
| 4h | 4 hours | ✅ | ✅ |
| 1d | 1 day | ✅ | ✅ |

## 🎯 Common Use Cases

### 1. Real-time Price Display
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/prices');
ws.onmessage = (event) => {
  const { symbol, price, change_24h } = JSON.parse(event.data);
  updatePriceDisplay(symbol, price, change_24h);
};
```

### 2. Historical Chart
```javascript
const response = await fetch(
  'http://localhost:8000/api/assets/SOL/ohlc?interval=1h&limit=100'
);
const { data } = await response.json();
renderChart(data);
```

### 3. Multi-symbol Dashboard
```javascript
const symbols = ['SOL', 'BTC', 'ETH'];
const prices = await Promise.all(
  symbols.map(symbol => 
    fetch(`http://localhost:8000/api/assets/${symbol}`).then(r => r.json())
  )
);
```

## 🐛 Troubleshooting

### No data received
1. Check if service is running: `curl http://localhost:8000/api/health`
2. Verify Backpack is enabled: `BACKPACK_ENABLED=true`
3. Check logs for connection errors

### OHLC data empty
1. Wait for candle close (may take up to 1 minute for 1m interval)
2. Use fallback: `?source=binance`
3. Check if symbol exists on Backpack

### WebSocket disconnects
1. Check network connectivity
2. Verify WebSocket URL
3. Add reconnection logic in client

## 📚 Next Steps

- [Full Documentation](./BACKPACK_TRADINGVIEW.md)
- [Architecture Overview](../architecture/ARCHITECTURE.md)
- [API Reference](../api/API_REFERENCE.md)
