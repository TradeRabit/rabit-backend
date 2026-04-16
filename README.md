# Rabit Backend

Backend service untuk Rabit dengan WebSocket (driftpy), Claude Agent SDK, dan REST API.

## ✨ Features

- ✅ **REST API** - FastAPI dengan auto-generated documentation
- ✅ **WebSocket** - Real-time price updates
- ✅ **Auto Conversation Compression** - Otomatis compress conversation ketika mencapai token limit
- ✅ **Memory Management** - Scoped memory per user dan global memory
- ✅ **Tool Calling System** - Comprehensive tool registry dengan detailed error handling
- ✅ **CoinGecko Integration** - Basic coin information dengan database caching
- 🚧 **Drift WebSocket** - Real-time market data (coming soon)

## 📁 Struktur Project

```
rabit-backend/
├── api/                 # REST API endpoints
│   ├── routes.py       # API routes
│   ├── models.py       # Response models
│   └── __init__.py
├── config/              # Konfigurasi aplikasi
├── agents/              # Claude Agent implementations
│   ├── core/           # BaseAgent & TradingAgent
│   ├── memory/         # Memory management
│   ├── compression/    # Auto compression
│   ├── tools/          # Tool registry
│   └── examples/       # Example tools
├── ws/                  # WebSocket & Market Data
│   ├── drift/          # Drift protocol WS
│   ├── binance/        # Binance OHLC data
│   ├── coingecko/      # CoinGecko integration
│   ├── services/       # Market data service
│   ├── handlers/       # Event handlers
│   └── models/         # Data models
├── models/              # Database models
├── utils/               # Utility functions
├── docs/                # Documentation
├── main.py              # FastAPI entry point
└── requirements.txt     # Dependencies
```

## 🚀 Quick Start

### 1. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables

```bash
cp .env.example .env
```

Edit `.env` dan tambahkan `ANTHROPIC_API_KEY` Anda.

### 4. Run Application

```bash
python main.py
```

Server akan berjalan di `http://localhost:8000`

## 📡 API Endpoints

### Base URL
```
http://localhost:8000
```

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

#### 1. Get Assets List
```bash
GET /api/assets
```

**Parameters:**
- `category` (optional): Filter by category (e.g., 'DeFi', 'Stablecoin')
- `limit` (optional): Maximum number of results (default: 50)

**Example:**
```bash
curl http://localhost:8000/api/assets
curl http://localhost:8000/api/assets?category=DeFi
```

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
    }
  ],
  "total": 20
}
```

#### 2. Get Asset Detail
```bash
GET /api/assets/{symbol}
```

**Example:**
```bash
curl http://localhost:8000/api/assets/BTC
```

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
    "explorer": "https://blockchain.info",
    "contract_address": null
  },
  "last_updated": "2024-01-01T00:00:00Z"
}
```

#### 3. Get OHLC Data (Chart)
```bash
GET /api/assets/{symbol}/ohlc
```

**Parameters:**
- `interval`: Candle interval (`1m`, `5m`, `15m`, `1h`, `4h`, `1d`)
- `limit`: Number of candles (default: 100, max: 1000)

**Example:**
```bash
curl "http://localhost:8000/api/assets/BTC/ohlc?interval=1h&limit=100"
```

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
    }
  ]
}
```

#### 4. WebSocket - Real-time Price Updates
```bash
WS /api/ws/prices
```

**JavaScript Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/prices');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Price update:', data);
  // { symbol: 'BTC', price: 65230.12, change_24h: 2.45, ... }
};
```

#### 5. Health Check
```bash
GET /api/health
```

**Example:**
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "Rabit Backend API"
}
```

## 📖 Complete API Documentation

Lihat [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) untuk dokumentasi lengkap dengan:
- Semua endpoints dan parameters
- Request/response examples
- Error handling
- WebSocket usage
- Code examples (JavaScript, Python, cURL)

## 📚 Documentation

**📖 [Complete Documentation Hub →](docs/README.md)**

Dokumentasi lengkap telah direorganisasi dengan struktur yang lebih rapi:

### Quick Links

#### 🚀 Getting Started
- **[Quick Start Guide](docs/getting-started/QUICKSTART.md)** - Get up and running in 5 minutes
- **[Features Overview](docs/getting-started/FEATURES.md)** - Explore what Rabit can do

#### 📡 API & Integration
- **[API Reference](docs/api/API_REFERENCE.md)** - Complete API documentation
- **[WebSocket Structure](docs/websocket/WS_STRUCTURE.md)** - Real-time data integration

#### 🤖 AI Agents
- **[Agent Structure](docs/agents/AGENTS_STRUCTURE.md)** - AI agent system
- **[Assistant Types](docs/agents/ASSISTANT_TYPES.md)** - Different assistant types

#### 📊 Data Sources
- **[Backpack Exchange](docs/websocket/BACKPACK_INTEGRATION.md)** - Backpack integration
- **[CoinGecko Integration](docs/integrations/COINGECKO_INTEGRATION.md)** - Coin information
- **[Data Sources Overview](docs/websocket/DATA_SOURCES.md)** - All data sources

#### 💻 Development
- **[Development Guide](docs/development/DEVELOPMENT.md)** - Development workflow
- **[Implementation Checklist](docs/development/IMPLEMENTATION_CHECKLIST.md)** - Feature tracking

### Documentation Categories

```
docs/
├── getting-started/    # Quick start & features
├── architecture/       # System design
├── api/               # API reference
├── agents/            # AI agents
├── websocket/         # Real-time data
├── integrations/      # Third-party services
├── tools/             # Available tools
└── development/       # Dev guides
```

**[→ Browse All Documentation](docs/README.md)** | **[→ Complete Index](docs/DOCS_INDEX.md)**

## 🎯 Frontend Integration

### JavaScript/TypeScript

```typescript
// services/api.ts
const API_BASE = 'http://localhost:8000/api';

export async function getAssets(category?: string) {
  const url = category 
    ? `${API_BASE}/assets?category=${category}`
    : `${API_BASE}/assets`;
  
  const response = await fetch(url);
  return response.json();
}

export async function getAssetDetail(symbol: string) {
  const response = await fetch(`${API_BASE}/assets/${symbol}`);
  return response.json();
}

export function connectPriceUpdates(onUpdate: (data: any) => void) {
  const ws = new WebSocket('ws://localhost:8000/api/ws/prices');
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onUpdate(data);
  };
  
  return ws;
}
```

### React Hook Example

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

## 🐳 Docker Setup

```bash
# Setup environment
make env

# Build dan start
make build
make up

# View logs
make logs
```

## 🛠️ Development

### Run Tests

```bash
# Test setup
python test_setup.py

# Test CoinGecko integration
python test_coingecko.py

# Test Drift WS (mock)
python test_drift_mock.py
```

### Run with Auto-reload

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

Edit `.env` file:

```bash
# Environment
ENVIRONMENT=development

# API Keys
ANTHROPIC_API_KEY=your_key_here

# Server
HOST=0.0.0.0
PORT=8000

# WebSocket
WS_HOST=localhost
WS_PORT=8765

# Drift
DRIFT_SUBSCRIBE_ASSETS=SOL,BTC,ETH,USDT,BNB
```

## 📊 Data Sources

### Real-time Data (Drift WS)
- Price, 24h %, Volume
- Open Interest, Funding Rate
- Market Cap, FDV, High/Low

### Static Data (CoinGecko)
- Description, Links, Categories
- Cached for 30 days

### Chart Data (Binance)
- OHLC data for TradingView

## 🚦 Status Codes

- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

## 🔍 Troubleshooting

### Port already in use
```bash
# Kill process on port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Module not found
```bash
pip install -r requirements.txt
```

### WebSocket connection failed
- Check if server is running
- Verify WebSocket URL
- Check firewall settings

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

**Version**: 1.0.0
**Last Updated**: 2024-01-01
