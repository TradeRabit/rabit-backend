# Data Sources

Dokumentasi tentang sumber data untuk aplikasi Rabit.

## 📊 Data Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (Mobile)                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Backend API (FastAPI)                   │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│  Drift WS    │          │  CoinGecko   │
│ (Real-time)  │          │  (Static)    │
└──────────────┘          └──────┬───────┘
                                 │
                                 ▼
                          ┌──────────────┐
                          │   Database   │
                          │    (JSON)    │
                          └──────────────┘
```

## 🔄 Data Sources

### 1. Drift WebSocket (Real-time Price Data)

**Purpose**: Real-time market data yang update setiap detik

**Data yang di-handle**:
- ✅ Price (current price)
- ✅ 24h % (price change percentage)
- ✅ 24h Vol (trading volume)
- ✅ Open Interest
- ✅ Funding Rate (1h)
- ✅ Market Cap
- ✅ FDV (Fully Diluted Valuation)
- ✅ High 24h
- ✅ Low 24h

**Update Frequency**: Real-time (setiap detik)

**Implementation**: `ws/drift/client.py`

**Usage**:
```python
from ws.drift import DriftWSClient
from ws.handlers import MarketDataHandler

handler = MarketDataHandler()
client = DriftWSClient(handler)

# Subscribe to price updates
await client.subscribe(["SOL-PERP", "BTC-PERP"])

# Get price
price_update = handler.get_price("SOL")
print(f"Price: ${price_update.price}")
print(f"24h Change: {price_update.change_24h}%")
print(f"Volume: ${price_update.volume_24h}")
print(f"Market Cap: ${price_update.market_cap}")
```

### 2. CoinGecko API (Basic Information)

**Purpose**: Static information yang jarang berubah

**Data yang di-handle**:
- ✅ Description (coin description)
- ✅ Links (website, twitter, telegram, github, explorer)
- ✅ Contract Address (for tokens)
- ✅ Categories (DeFi, Layer 1, etc)

**Update Frequency**: Setiap 30 hari (cached di database)

**Implementation**: `ws/coingecko/client.py`

**Usage**:
```python
from ws.services import get_market_service

service = get_market_service()

# Get coin info (from cache or CoinGecko)
coin_info = await service.get_coin_info("BTC")
print(f"Name: {coin_info.name}")
print(f"Description: {coin_info.description}")
print(f"Website: {coin_info.links.website}")
print(f"Twitter: {coin_info.links.twitter}")
```

### 3. Frontend (Logo/Icons)

**Purpose**: Visual assets

**Data yang di-handle**:
- ✅ Coin logos/icons
- ✅ UI icons

**Implementation**: Frontend component (`CryptoIcon`)

**Note**: Logo tidak perlu di-fetch dari backend, sudah di-handle di frontend.

## 📦 Data Models

### PriceUpdate (from Drift WS)

```python
{
    "symbol": "BTC",
    "price": 65230.12,
    "change_24h": 2.45,
    "volume_24h": 28500000000,
    "open_interest": 5000000,
    "funding_rate": 0.01,
    "market_cap": 1280000000000,
    "fdv": 1370000000000,
    "high_24h": 66000.00,
    "low_24h": 64500.00,
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### CoinInfo (from CoinGecko)

```python
{
    "id": "bitcoin",
    "symbol": "BTC",
    "name": "Bitcoin",
    "description": "Bitcoin is the first decentralized cryptocurrency...",
    "links": {
        "website": "https://bitcoin.org",
        "twitter": "https://twitter.com/bitcoin",
        "telegram": None,
        "github": "https://github.com/bitcoin/bitcoin",
        "explorer": "https://blockchain.info"
    },
    "contract_address": {},
    "categories": ["Cryptocurrency", "Layer 1"],
    "last_updated": "2024-01-01T00:00:00Z"
}
```

## 🔄 Data Flow

### Startup Flow

```
1. Initialize CoinGecko Service
   ↓
2. Load coin info from database
   ↓
3. If stale (>30 days), fetch from CoinGecko
   ↓
4. Save to database
   ↓
5. Start Drift WS connection
   ↓
6. Subscribe to price updates
   ↓
7. Ready to serve requests
```

### Request Flow

```
Frontend Request
   ↓
Backend API
   ↓
┌──────────────┴──────────────┐
│                             │
▼                             ▼
Get Price Data          Get Coin Info
(from Drift WS)         (from Database)
│                             │
└──────────────┬──────────────┘
               ▼
        Combine & Return
               ▼
          Frontend
```

## 🎯 API Response Example

```json
{
  "symbol": "BTC",
  "name": "Bitcoin",
  
  // Real-time data (from Drift WS)
  "price": 65230.12,
  "change_24h": 2.45,
  "volume_24h": 28500000000,
  "market_cap": 1280000000000,
  "fdv": 1370000000000,
  "high_24h": 66000.00,
  "low_24h": 64500.00,
  "open_interest": 5000000,
  "funding_rate": 0.01,
  
  // Static data (from CoinGecko/Database)
  "description": "Bitcoin is the first decentralized cryptocurrency...",
  "website": "https://bitcoin.org",
  "twitter": "https://twitter.com/bitcoin",
  "explorer": "https://blockchain.info",
  "categories": ["Cryptocurrency", "Layer 1"]
}
```

## ⚙️ Configuration

### Drift WS

```python
# .env
DRIFT_SUBSCRIBE_ASSETS=SOL,BTC,ETH,USDT,BNB
DRIFT_WS_URL=wss://drift-ws.example.com
```

### CoinGecko

```python
# No configuration needed
# Free tier: 10-50 calls/minute
# Rate limiting handled automatically
```

### Database

```python
# Database path
DB_PATH=data/coins.json

# Cache duration
CACHE_DURATION_DAYS=30
```

## 📝 Best Practices

### 1. Price Data
- ✅ Always use Drift WS for price data
- ✅ Never fetch price from CoinGecko
- ✅ Cache price in memory (MarketDataHandler)
- ✅ Update every second from WS

### 2. Coin Info
- ✅ Always check database first
- ✅ Only fetch from CoinGecko if stale (>30 days)
- ✅ Save to database after fetch
- ✅ Respect rate limits (2 sec delay)

### 3. Frontend
- ✅ Use local icons/logos
- ✅ Don't fetch logo from backend
- ✅ Cache API responses
- ✅ Handle loading states

## 🔍 Troubleshooting

### Price data is None
- Check Drift WS connection
- Verify symbol is subscribed
- Check MarketDataHandler

### Coin info not found
- Check symbol mapping in `market_service.py`
- Verify CoinGecko ID
- Check database file

### Rate limit exceeded
- Wait 60 seconds (handled automatically)
- Reduce refresh frequency
- Use database cache

## 📚 Related Documentation

- [COINGECKO_INTEGRATION.md](COINGECKO_INTEGRATION.md) - CoinGecko integration details
- [WS_STRUCTURE.md](WS_STRUCTURE.md) - WebSocket module structure
- [API_REFERENCE.md](API_REFERENCE.md) - API reference

---

**Last Updated**: 2024-01-01
**Version**: 1.0.0
