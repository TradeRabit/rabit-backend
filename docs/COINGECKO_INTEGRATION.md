# CoinGecko Integration

Dokumentasi untuk integrasi CoinGecko API dan database untuk menyimpan informasi coin.

## 📋 Overview

Integrasi CoinGecko menyediakan:
- **Coin Information**: Description, links, logo, categories
- **Market Data**: Market cap, FDV, TVL, high/low 24h
- **Database Caching**: Menyimpan data permanen untuk menghindari rate limit
- **Combined Data**: Menggabungkan data real-time dari Drift dengan data static dari CoinGecko

## 🏗️ Architecture

```
┌─────────────────┐
│  Mobile App     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Market Service  │ ◄─── Menggabungkan data
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│ Drift  │ │CoinGecko │
│   WS   │ │   API    │
└────────┘ └─────┬────┘
                 │
                 ▼
           ┌──────────┐
           │ Database │
           │  (JSON)  │
           └──────────┘
```

## 📁 Structure

```
ws/
├── models/
│   ├── market_data.py      # PriceUpdate (extended)
│   └── coin_info.py        # CoinInfo, CoinMarketData, CompleteCoinData
├── coingecko/
│   ├── client.py           # CoinGecko API client
│   ├── database.py         # JSON database untuk caching
│   └── __init__.py
├── services/
│   ├── market_service.py   # Service layer
│   └── __init__.py
└── __init__.py
```

## 🔧 Components

### 1. CoinGecko Client (`ws/coingecko/client.py`)

Client untuk mengakses CoinGecko Free API dengan rate limiting.

**Features:**
- Rate limiting (2 detik delay antar request)
- Auto retry pada rate limit exceeded
- Search coin by symbol
- Get coin info (description, links, etc)
- Get market data (market cap, FDV, etc)

**Usage:**
```python
from ws.coingecko import get_coingecko_client

client = get_coingecko_client()

# Get coin info
coin_info = await client.get_coin_info("bitcoin")

# Get market data for multiple coins
market_data = await client.get_market_data(["bitcoin", "ethereum"])

# Search coin by symbol
coin_id = await client.search_coin_by_symbol("BTC")
```

### 2. Coin Database (`ws/coingecko/database.py`)

Simple JSON-based database untuk menyimpan coin info secara permanen.

**Features:**
- Save/load coin info to/from JSON file
- Check if data is stale (default: 30 days)
- Get database statistics
- Auto-save on updates

**Usage:**
```python
from ws.coingecko import get_coin_database

db = get_coin_database()

# Save coin info
db.save_coin_info(coin_info)

# Get coin info
coin_info = db.get_coin_info("BTC")

# Check if stale
if db.is_stale("BTC", max_age_days=30):
    # Refresh from CoinGecko
    pass

# Get stats
stats = db.get_stats()
```

### 3. Market Service (`ws/services/market_service.py`)

Service layer yang menggabungkan data dari Drift WS dan CoinGecko.

**Features:**
- Ensure coin info exists (fetch if needed)
- Get complete coin data (info + market)
- Refresh market data from CoinGecko
- Initialize coins on startup
- Get multiple coins at once

**Usage:**
```python
from ws.services import get_market_service

service = get_market_service()

# Get complete coin data
data = await service.get_complete_coin_data("BTC")
print(f"Price: ${data.market.price}")
print(f"Market Cap: ${data.market.market_cap}")
print(f"Description: {data.info.description}")

# Get multiple coins
all_data = await service.get_multiple_coins(["BTC", "ETH", "SOL"])

# Refresh market data (call periodically)
await service.refresh_market_data_from_coingecko(["BTC", "ETH", "SOL"])

# Initialize on startup
await service.initialize_coins(["BTC", "ETH", "SOL"])
```

## 📊 Data Models

### CoinInfo
```python
{
    "id": "bitcoin",
    "symbol": "BTC",
    "name": "Bitcoin",
    "image_url": "https://...",
    "description": "Bitcoin is...",
    "links": {
        "website": "https://bitcoin.org",
        "twitter": "https://twitter.com/bitcoin",
        "explorer": "https://blockchain.info"
    },
    "categories": ["Cryptocurrency", "Layer 1"],
    "last_updated": "2024-01-01T00:00:00Z"
}
```

### CoinMarketData
```python
{
    "symbol": "BTC",
    "price": 65230.12,
    "change_24h": 2.45,
    "volume_24h": 28500000000,
    "market_cap": 1280000000000,
    "fdv": 1370000000000,
    "high_24h": 66000.00,
    "low_24h": 64500.00,
    "open_interest": 5000000,
    "funding_rate": 0.01,
    "last_updated": "2024-01-01T00:00:00Z"
}
```

### CompleteCoinData
```python
{
    "info": { ... },  # CoinInfo
    "market": { ... } # CoinMarketData
}
```

## 🚀 Usage Flow

### 1. Startup Initialization

```python
from ws.services import get_market_service

service = get_market_service()

# Initialize coin info for all symbols
symbols = ["BTC", "ETH", "SOL", "USDT", "BNB"]
await service.initialize_coins(symbols)
```

### 2. Real-time Price Updates (Drift WS)

```python
from ws.drift import DriftWSClient
from ws.handlers import MarketDataHandler

handler = MarketDataHandler()
client = DriftWSClient(handler)

# Subscribe to price updates
await client.subscribe(["SOL-PERP", "BTC-PERP"])

# Prices are automatically updated in handler
```

### 3. Periodic Market Data Refresh (CoinGecko)

```python
import asyncio
from ws.services import get_market_service

async def refresh_market_data():
    service = get_market_service()
    symbols = ["BTC", "ETH", "SOL"]
    
    while True:
        # Refresh every hour
        await service.refresh_market_data_from_coingecko(symbols)
        await asyncio.sleep(3600)  # 1 hour

# Run in background
asyncio.create_task(refresh_market_data())
```

### 4. Get Complete Data for Frontend

```python
from ws.services import get_market_service

service = get_market_service()

# Get data for single coin
data = await service.get_complete_coin_data("BTC")

# Return to frontend
return {
    "symbol": data.market.symbol,
    "name": data.info.name,
    "price": data.market.price,
    "change_24h": data.market.change_24h,
    "volume_24h": data.market.volume_24h,
    "market_cap": data.market.market_cap,
    "fdv": data.market.fdv,
    "high_24h": data.market.high_24h,
    "low_24h": data.market.low_24h,
    "open_interest": data.market.open_interest,
    "funding_rate": data.market.funding_rate,
    "description": data.info.description,
    "image_url": data.info.image_url,
    "links": data.info.links
}
```

## ⚙️ Configuration

No additional configuration needed. The service uses:
- **Database Path**: `data/coins.json` (auto-created)
- **Rate Limit**: 2 seconds between requests
- **Cache Duration**: 30 days (configurable)

## 🧪 Testing

Run the test file:

```bash
python test_coingecko.py
```

This will:
1. Fetch coin info from CoinGecko
2. Save to database
3. Get complete coin data
4. Refresh market data
5. Test multiple coins at once

## 📝 Rate Limits

**CoinGecko Free Tier:**
- 10-50 calls/minute
- No API key required
- Rate limiting handled automatically

**Best Practices:**
- Cache coin info in database (refresh every 30 days)
- Refresh market data every 1 hour (not every request)
- Use Drift WS for real-time price updates
- Batch requests when possible

## 🔄 Data Flow

```
1. Startup:
   - Initialize coin info from database or CoinGecko
   - Start Drift WS for real-time prices

2. Real-time Updates:
   - Drift WS → Price, 24h %, Volume, OI, Funding
   - Updates every second

3. Periodic Refresh (every 1 hour):
   - CoinGecko → Market Cap, FDV, High/Low 24h
   - Updates in background

4. Frontend Request:
   - Combine Drift + CoinGecko data
   - Return complete coin data
```

## 🎯 Supported Symbols

Default mapping (can be extended):
- BTC, ETH, SOL, USDT, USDC
- BNB, XRP, ADA, AVAX, DOT
- MATIC, LINK, UNI, ATOM, LTC
- NEAR, APT, ARB, OP, SUI

## 📚 API Reference

### MarketDataService

#### `ensure_coin_info(symbol: str) -> Optional[CoinInfo]`
Ensure coin info exists, fetch from CoinGecko if needed.

#### `get_complete_coin_data(symbol: str) -> Optional[CompleteCoinData]`
Get complete coin data (info + market).

#### `get_multiple_coins(symbols: List[str]) -> Dict[str, CompleteCoinData]`
Get data for multiple coins at once.

#### `refresh_market_data_from_coingecko(symbols: List[str])`
Refresh market data from CoinGecko (call periodically).

#### `initialize_coins(symbols: List[str])`
Initialize coin info for all symbols (call on startup).

#### `get_database_stats() -> Dict`
Get database statistics.

## 🐛 Troubleshooting

### Rate Limit Exceeded
- Wait 60 seconds (handled automatically)
- Reduce refresh frequency
- Use database cache

### Coin Not Found
- Check symbol mapping in `market_service.py`
- Use `search_coin_by_symbol()` to find CoinGecko ID
- Add to symbol_to_id mapping

### Database Issues
- Check `data/coins.json` file
- Clear database: `db.clear()`
- Re-initialize coins

## 🔮 Future Enhancements

- [ ] Add PostgreSQL/MongoDB support
- [ ] Add more coin mappings
- [ ] Add TVL data from DeFiLlama
- [ ] Add historical data caching
- [ ] Add WebSocket for CoinGecko Pro
- [ ] Add price alerts
- [ ] Add portfolio tracking

---

**Last Updated**: 2024-01-01
**Version**: 1.0.0
