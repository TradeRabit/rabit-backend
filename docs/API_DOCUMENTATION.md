# API Documentation

Complete API documentation untuk Rabit Backend.

## 📚 Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Assets](#assets)
  - [Chart Data](#chart-data)
  - [WebSocket](#websocket)
  - [System](#system)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

---

## 🌐 Base URL

```
Development: http://localhost:8000
Production: https://api.rabit.example.com
```

## 🔐 Authentication

Currently, no authentication is required. Authentication will be added in future versions.

---

## 📡 Endpoints

### Assets

#### GET /api/assets

Get list of all available assets with price data.

**Parameters:**
- `category` (optional, string): Filter by category (e.g., 'DeFi', 'Stablecoin')
- `limit` (optional, integer): Maximum number of assets to return (default: 50)

**Response:**
```json
{
  "assets": [
    {
      "symbol": "BTC",
      "name": "Bitcoin",
      "price": 65230.12,
      "change_24h": 2.45,
      "categories": ["Cryptocurrency", "Layer 1"]
    },
    {
      "symbol": "ETH",
      "name": "Ethereum",
      "price": 3718.71,
      "change_24h": 4.66,
      "categories": ["Smart Contract Platform", "Layer 1"]
    }
  ],
  "total": 20
}
```

**Example:**
```bash
# Get all assets
curl http://localhost:8000/api/assets

# Filter by category
curl http://localhost:8000/api/assets?category=DeFi

# Limit results
curl http://localhost:8000/api/assets?limit=10
```

---

#### GET /api/assets/{symbol}

Get detailed information for a specific asset.

**Parameters:**
- `symbol` (required, path): Asset symbol (e.g., 'BTC', 'ETH', 'SOL')

**Response:**
```json
{
  "symbol": "BTC",
  "name": "Bitcoin",
  "price": 65230.12,
  "change_24h": 2.45,
  "volume_24h": 28500000000,
  "high_24h": 66000.00,
  "low_24h": 64500.00,
  "market_cap": 1280000000000,
  "fdv": 1370000000000,
  "tvl": null,
  "open_interest": 5000000,
  "funding_rate": 0.01,
  "description": "Bitcoin is the first decentralized cryptocurrency...",
  "categories": ["Cryptocurrency", "Layer 1"],
  "links": {
    "website": "https://bitcoin.org",
    "twitter": "https://twitter.com/bitcoin",
    "telegram": null,
    "github": "https://github.com/bitcoin/bitcoin",
    "explorer": "https://blockchain.info",
    "contract_address": null
  },
  "last_updated": "2024-01-01T00:00:00Z"
}
```

**Example:**
```bash
curl http://localhost:8000/api/assets/BTC
curl http://localhost:8000/api/assets/ETH
curl http://localhost:8000/api/assets/SOL
```

**Error Responses:**
```json
// 404 - Asset not found
{
  "detail": "Asset 'XYZ' not found"
}

// 404 - Price data not available
{
  "detail": "Price data for 'BTC' not available"
}
```

---

### Chart Data

#### GET /api/assets/{symbol}/ohlc

Get OHLC (candlestick) data for charting.

**Parameters:**
- `symbol` (required, path): Asset symbol (e.g., 'BTC', 'ETH')
- `interval` (optional, query): Candle interval - `1m`, `5m`, `15m`, `1h`, `4h`, `1d` (default: `1h`)
- `limit` (optional, query): Number of candles to return (default: 100, max: 1000)

**Response:**
```json
{
  "symbol": "BTC",
  "interval": "1h",
  "data": [
    {
      "timestamp": 1704067200000,
      "open": 65000.00,
      "high": 65500.00,
      "low": 64800.00,
      "close": 65230.12,
      "volume": 1250000000
    },
    {
      "timestamp": 1704070800000,
      "open": 65230.12,
      "high": 65800.00,
      "low": 65100.00,
      "close": 65450.00,
      "volume": 1180000000
    }
  ]
}
```

**Example:**
```bash
# Get 1h candles
curl http://localhost:8000/api/assets/BTC/ohlc

# Get 15m candles
curl http://localhost:8000/api/assets/BTC/ohlc?interval=15m

# Get last 500 candles
curl http://localhost:8000/api/assets/BTC/ohlc?limit=500

# Get 1d candles for last 30 days
curl http://localhost:8000/api/assets/BTC/ohlc?interval=1d&limit=30
```

**Error Responses:**
```json
// 400 - Invalid interval
{
  "detail": "Invalid interval. Must be one of: 1m, 5m, 15m, 1h, 4h, 1d"
}

// 404 - OHLC data not available
{
  "detail": "OHLC data for 'BTC' not available"
}
```

---

### WebSocket

#### WS /api/ws/prices

WebSocket endpoint for real-time price updates.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/prices');

ws.onopen = () => {
  console.log('Connected to price updates');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Price update:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from price updates');
};
```

**Message Format:**
```json
{
  "symbol": "BTC",
  "price": 65230.12,
  "change_24h": 2.45,
  "volume_24h": 28500000000,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Ping/Pong:**
```javascript
// Send ping to keep connection alive
ws.send('ping');

// Server will respond with 'pong'
```

**React Example:**
```typescript
import { useEffect, useState } from 'react';

function usePriceUpdates() {
  const [prices, setPrices] = useState<Record<string, number>>({});
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/api/ws/prices');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setPrices(prev => ({
        ...prev,
        [data.symbol]: data.price
      }));
    };
    
    return () => ws.close();
  }, []);
  
  return prices;
}
```

---

### System

#### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "Rabit Backend API"
}
```

**Example:**
```bash
curl http://localhost:8000/api/health
```

---

#### GET /

Root endpoint - API information.

**Response:**
```json
{
  "name": "Rabit Backend API",
  "version": "1.0.0",
  "description": "Backend API untuk Rabit Mobile App",
  "docs": "/docs",
  "redoc": "/redoc",
  "health": "/api/health"
}
```

---

## 📋 Response Format

### Success Response

All successful responses follow this format:

```json
{
  // Response data
}
```

### Error Response

All error responses follow this format:

```json
{
  "detail": "Error message"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (resource not found)
- `500` - Internal Server Error

---

## ⚠️ Error Handling

### Common Errors

#### 404 - Asset Not Found
```json
{
  "detail": "Asset 'XYZ' not found"
}
```

**Solution**: Check if the symbol is correct and supported.

#### 404 - Price Data Not Available
```json
{
  "detail": "Price data for 'BTC' not available"
}
```

**Solution**: Wait for Drift WS to connect and start sending price updates.

#### 400 - Invalid Interval
```json
{
  "detail": "Invalid interval. Must be one of: 1m, 5m, 15m, 1h, 4h, 1d"
}
```

**Solution**: Use one of the supported intervals.

#### 500 - Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

**Solution**: Check server logs for details.

---

## 🚦 Rate Limiting

Currently, no rate limiting is implemented. Rate limiting will be added in future versions.

**Recommended Limits:**
- REST API: 100 requests per minute
- WebSocket: 1 connection per client

---

## 📝 Examples

### JavaScript/TypeScript

```typescript
// api.ts
const API_BASE = 'http://localhost:8000/api';

export async function getAssets(category?: string) {
  const url = category 
    ? `${API_BASE}/assets?category=${category}`
    : `${API_BASE}/assets`;
  
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
}

export async function getAssetDetail(symbol: string) {
  const response = await fetch(`${API_BASE}/assets/${symbol}`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
}

export async function getOHLCData(
  symbol: string,
  interval: string = '1h',
  limit: number = 100
) {
  const response = await fetch(
    `${API_BASE}/assets/${symbol}/ohlc?interval=${interval}&limit=${limit}`
  );
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
}

export function connectPriceUpdates(
  onUpdate: (data: any) => void,
  onError?: (error: any) => void
) {
  const ws = new WebSocket('ws://localhost:8000/api/ws/prices');
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onUpdate(data);
  };
  
  ws.onerror = (error) => {
    if (onError) onError(error);
  };
  
  return ws;
}
```

### Python

```python
import requests
import websocket
import json

API_BASE = 'http://localhost:8000/api'

def get_assets(category=None):
    """Get list of assets"""
    params = {'category': category} if category else {}
    response = requests.get(f'{API_BASE}/assets', params=params)
    response.raise_for_status()
    return response.json()

def get_asset_detail(symbol):
    """Get asset detail"""
    response = requests.get(f'{API_BASE}/assets/{symbol}')
    response.raise_for_status()
    return response.json()

def get_ohlc_data(symbol, interval='1h', limit=100):
    """Get OHLC data"""
    params = {'interval': interval, 'limit': limit}
    response = requests.get(f'{API_BASE}/assets/{symbol}/ohlc', params=params)
    response.raise_for_status()
    return response.json()

def connect_price_updates(on_message):
    """Connect to WebSocket for price updates"""
    def on_ws_message(ws, message):
        data = json.loads(message)
        on_message(data)
    
    ws = websocket.WebSocketApp(
        'ws://localhost:8000/api/ws/prices',
        on_message=on_ws_message
    )
    ws.run_forever()
```

### cURL

```bash
# Get all assets
curl -X GET http://localhost:8000/api/assets

# Get DeFi assets
curl -X GET "http://localhost:8000/api/assets?category=DeFi"

# Get BTC detail
curl -X GET http://localhost:8000/api/assets/BTC

# Get OHLC data
curl -X GET "http://localhost:8000/api/assets/BTC/ohlc?interval=1h&limit=100"

# Health check
curl -X GET http://localhost:8000/api/health
```

---

## 🔧 Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- View all endpoints
- See request/response schemas
- Test endpoints directly from the browser
- Download OpenAPI specification

---

## 📊 Data Sources

### Real-time Data (Drift WS)
- Price
- 24h Change %
- 24h Volume
- Open Interest
- Funding Rate
- Market Cap
- FDV
- High/Low 24h

### Static Data (CoinGecko)
- Name
- Description
- Links
- Contract Address
- Categories

### Chart Data (Binance)
- OHLC data for TradingView

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 3. Run Server

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test API

```bash
# Health check
curl http://localhost:8000/api/health

# Get assets
curl http://localhost:8000/api/assets

# View docs
open http://localhost:8000/docs
```

---

## 📞 Support

For issues or questions:
- Check the [troubleshooting guide](DEVELOPMENT.md#troubleshooting)
- Review [examples](../examples/)
- Open an issue on GitHub

---

**Last Updated**: 2024-01-01
**API Version**: 1.0.0
