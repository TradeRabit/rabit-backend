# Mobile Data Requirements

Dokumentasi lengkap data yang dibutuhkan oleh Rabit Mobile App.

## 📱 Home Screen (AssetExplorer)

### Data yang Dibutuhkan:

```typescript
interface AssetListItem {
  // Identifiers
  symbol: string;        // "BTC", "ETH", "SOL"
  name: string;          // "Bitcoin", "Ethereum", "Solana"
  
  // Price Data (dari Drift WS)
  price: number;         // 65230.12
  change_24h: number;    // 2.45 (percentage)
  isPositive: boolean;   // true/false (derived from change_24h)
}
```

### Filters yang Dibutuhkan:
- All
- Favorite (client-side)
- Crypto
- Stablecoin
- DeFi

**Note**: Filter categories bisa diambil dari `CoinInfo.categories` dari CoinGecko.

---

## 📊 Asset Detail Page

### 1. Header Section

```typescript
interface AssetHeader {
  symbol: string;        // "BTC"
  name: string;          // "Bitcoin"
  price: number;         // 65230.12
  change_24h: number;    // 2.45
  isPositive: boolean;   // true/false
}
```

### 2. Stats Section

```typescript
interface AssetStats {
  // Dari Drift WS
  tvl?: number;          // Total Value Locked (untuk DeFi)
  market_cap: number;    // Market capitalization
  fdv: number;           // Fully Diluted Valuation
  volume_24h: number;    // 24h trading volume
  high_24h: number;      // 24h high price
  low_24h: number;       // 24h low price
  
  // Tambahan dari Drift
  open_interest?: number;  // Open interest
  funding_rate?: number;   // Funding rate (1h)
}
```

**Stats yang ditampilkan**:
1. TVL - `$145.5M`
2. Market cap - `$184.4B`
3. FDV - `$189.9B`
4. 1 day volume - `$232.4M`
5. High - `$66,000.00`
6. Low - `$64,500.00`

### 3. About Section

```typescript
interface AssetAbout {
  description: string;   // Coin description (dari CoinGecko)
}
```

### 4. Links Section

```typescript
interface AssetLinks {
  contract_address?: string;  // "0xdAC1...1ec7" (shortened)
  explorer?: string;          // "https://etherscan.io" (Etherscan/Solscan)
  website?: string;           // "https://bitcoin.org"
  twitter?: string;           // "https://twitter.com/bitcoin"
}
```

**Links yang ditampilkan**:
1. Contract Address (dengan icon Copy)
2. Explorer (Etherscan/Solscan)
3. Website (dengan icon Globe)
4. Twitter (dengan icon X)

### 5. Chart Section (Future)

```typescript
interface ChartData {
  // OHLC data untuk TradingView
  ohlc: OHLCData[];
  
  // Timeframes
  timeframe: '15m' | '1H' | '1D' | '1W' | '1M';
  
  // Chart type
  type: 'Price' | 'Volume';
}
```

---

## 🎯 Complete API Response Format

### Endpoint: `GET /api/assets` (List)

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
  ]
}
```

### Endpoint: `GET /api/assets/{symbol}` (Detail)

```json
{
  // Basic Info
  "symbol": "BTC",
  "name": "Bitcoin",
  
  // Price Data (Real-time dari Drift WS)
  "price": 65230.12,
  "change_24h": 2.45,
  "volume_24h": 28500000000,
  "high_24h": 66000.00,
  "low_24h": 64500.00,
  
  // Market Data (dari Drift WS)
  "market_cap": 1280000000000,
  "fdv": 1370000000000,
  "tvl": null,
  "open_interest": 5000000,
  "funding_rate": 0.01,
  
  // Static Info (dari CoinGecko)
  "description": "Bitcoin is the first decentralized cryptocurrency...",
  "categories": ["Cryptocurrency", "Layer 1"],
  
  // Links (dari CoinGecko)
  "links": {
    "website": "https://bitcoin.org",
    "twitter": "https://twitter.com/bitcoin",
    "explorer": "https://blockchain.info",
    "contract_address": null
  },
  
  // Metadata
  "last_updated": "2024-01-01T00:00:00Z"
}
```

---

## ✅ Data yang Sudah Tersedia di Backend

### Dari Drift WS (Real-time):
- ✅ Price
- ✅ 24h % (change_24h)
- ✅ 24h Volume (volume_24h)
- ✅ Open Interest
- ✅ Funding Rate
- ✅ Market Cap
- ✅ FDV
- ✅ High 24h
- ✅ Low 24h

### Dari CoinGecko (Static):
- ✅ Name
- ✅ Description
- ✅ Links (website, twitter, explorer)
- ✅ Contract Address
- ✅ Categories

---

## ❌ Data yang Belum Tersedia

### 1. TVL (Total Value Locked)
**Status**: ❌ Belum ada
**Source**: Perlu integrasi dengan DeFiLlama API
**Priority**: Medium (hanya untuk DeFi tokens)

**Solution**:
```python
# Tambahkan di ws/defi/defillama.py
async def get_tvl(protocol: str) -> float:
    # Fetch from DeFiLlama API
    pass
```

### 2. OHLC Data untuk Chart
**Status**: ⚠️ Partial (ada scaffold di Binance)
**Source**: Binance History Downloader
**Priority**: High (untuk chart)

**Solution**:
```python
# Sudah ada di ws/binance/history.py
# Perlu diaktifkan dan diintegrasikan
```

### 3. Filter by Category
**Status**: ✅ Data ada, perlu endpoint
**Source**: CoinGecko categories
**Priority**: Low (bisa di-handle client-side)

**Solution**:
```python
# Endpoint baru
GET /api/assets?category=DeFi
GET /api/assets?category=Stablecoin
```

---

## 🔧 Yang Perlu Ditambahkan

### 1. REST API Endpoints

```python
# main.py atau api/routes.py

from fastapi import FastAPI, HTTPException
from ws.services import get_market_service
from ws.handlers import MarketDataHandler

app = FastAPI()

@app.get("/api/assets")
async def get_assets(category: Optional[str] = None):
    """Get list of assets"""
    service = get_market_service()
    handler = MarketDataHandler()
    
    # Get all symbols
    symbols = ["BTC", "ETH", "SOL", "USDT", "BNB", ...]
    
    assets = []
    for symbol in symbols:
        # Get coin info
        coin_info = await service.get_coin_info(symbol)
        
        # Get price data
        price_update = handler.get_price(symbol)
        
        if coin_info and price_update:
            # Filter by category if provided
            if category and category not in coin_info.categories:
                continue
            
            assets.append({
                "symbol": symbol,
                "name": coin_info.name,
                "price": price_update.price,
                "change_24h": price_update.change_24h,
                "categories": coin_info.categories
            })
    
    return {"assets": assets}


@app.get("/api/assets/{symbol}")
async def get_asset_detail(symbol: str):
    """Get asset detail"""
    service = get_market_service()
    handler = MarketDataHandler()
    
    # Get coin info
    coin_info = await service.get_coin_info(symbol.upper())
    if not coin_info:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Get price data
    price_update = handler.get_price(symbol.upper())
    if not price_update:
        raise HTTPException(status_code=404, detail="Price data not available")
    
    return {
        "symbol": symbol.upper(),
        "name": coin_info.name,
        "price": price_update.price,
        "change_24h": price_update.change_24h,
        "volume_24h": price_update.volume_24h,
        "high_24h": price_update.high_24h,
        "low_24h": price_update.low_24h,
        "market_cap": price_update.market_cap,
        "fdv": price_update.fdv,
        "tvl": price_update.tvl,
        "open_interest": price_update.open_interest,
        "funding_rate": price_update.funding_rate,
        "description": coin_info.description,
        "categories": coin_info.categories,
        "links": {
            "website": coin_info.links.website if coin_info.links else None,
            "twitter": coin_info.links.twitter if coin_info.links else None,
            "explorer": coin_info.links.explorer if coin_info.links else None,
            "contract_address": list(coin_info.contract_address.values())[0] if coin_info.contract_address else None
        },
        "last_updated": price_update.timestamp.isoformat()
    }
```

### 2. WebSocket Endpoint (untuk real-time updates)

```python
from fastapi import WebSocket

@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """WebSocket for real-time price updates"""
    await websocket.accept()
    
    handler = MarketDataHandler()
    
    # Subscribe to price updates
    async def on_price_update(price_update):
        await websocket.send_json({
            "symbol": price_update.symbol,
            "price": price_update.price,
            "change_24h": price_update.change_24h
        })
    
    handler.subscribe("price:*", on_price_update)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except:
        pass
```

### 3. OHLC Data Endpoint

```python
@app.get("/api/assets/{symbol}/ohlc")
async def get_ohlc_data(
    symbol: str,
    interval: str = "1h",
    limit: int = 100
):
    """Get OHLC data for chart"""
    from ws.binance import BinanceHistoryDownloader
    
    downloader = BinanceHistoryDownloader()
    ohlc_data = await downloader.download_history(
        symbol=symbol,
        interval=interval,
        limit=limit
    )
    
    return {
        "symbol": symbol,
        "interval": interval,
        "data": ohlc_data
    }
```

---

## 📋 Implementation Checklist

### Phase 1: Basic API (Priority: High)
- [ ] Create FastAPI app structure
- [ ] Add `/api/assets` endpoint (list)
- [ ] Add `/api/assets/{symbol}` endpoint (detail)
- [ ] Add error handling
- [ ] Add CORS configuration
- [ ] Test with mobile app

### Phase 2: Real-time Updates (Priority: High)
- [ ] Add WebSocket endpoint `/ws/prices`
- [ ] Integrate with MarketDataHandler
- [ ] Test real-time updates
- [ ] Add reconnection logic

### Phase 3: Chart Data (Priority: Medium)
- [ ] Activate Binance history downloader
- [ ] Add `/api/assets/{symbol}/ohlc` endpoint
- [ ] Test with TradingView chart
- [ ] Add caching for OHLC data

### Phase 4: Additional Features (Priority: Low)
- [ ] Add TVL data (DeFiLlama integration)
- [ ] Add filter by category
- [ ] Add search functionality
- [ ] Add pagination

---

## 🎨 Frontend Integration Example

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

// WebSocket for real-time updates
export function connectPriceUpdates(onUpdate: (data: any) => void) {
  const ws = new WebSocket('ws://localhost:8000/ws/prices');
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onUpdate(data);
  };
  
  return ws;
}
```

---

## 📝 Summary

### ✅ Data Sudah Tersedia:
- Price, 24h %, Volume, OI, Funding (Drift WS)
- Market Cap, FDV, High/Low (Drift WS)
- Description, Links, Categories (CoinGecko)

### ⚠️ Yang Perlu Ditambahkan:
1. **REST API Endpoints** (High Priority)
   - GET /api/assets
   - GET /api/assets/{symbol}
   
2. **WebSocket Endpoint** (High Priority)
   - WS /ws/prices

3. **OHLC Data** (Medium Priority)
   - GET /api/assets/{symbol}/ohlc

4. **TVL Data** (Low Priority)
   - Integrasi DeFiLlama

### 🚀 Next Steps:
1. Buat FastAPI app structure
2. Implement REST API endpoints
3. Test dengan mobile app
4. Add WebSocket untuk real-time updates
5. Integrate OHLC data untuk chart

---

**Last Updated**: 2024-01-01
**Version**: 1.0.0
