# Trading Assets Configuration

## 📋 Overview

`TRADING_ASSETS` adalah konfigurasi terpusat untuk semua trading symbols yang digunakan di seluruh aplikasi. Ini menggantikan `DRIFT_ASSETS` yang lebih spesifik, sehingga lebih mudah untuk integrasi dengan WebSocket sources lain.

## 🎯 Purpose

**Before (Specific):**
```env
DRIFT_ASSETS=BTC,ETH,SOL,...
BINANCE_ASSETS=BTC,ETH,SOL,...  # Duplicate!
SERUM_ASSETS=BTC,ETH,SOL,...    # Duplicate!
```

**After (Centralized):**
```env
TRADING_ASSETS=BTC,ETH,SOL,...  # Single source of truth
```

## 🔧 Configuration

### Environment Variable

```env
# Trading Assets (used by all WebSocket sources)
TRADING_ASSETS=BTC,ETH,SOL,DOGE,BNB,SUI,APT,ARB,RENDER,XRP,INJ,LINK,PYTH,JTO,AVAX,WIF,JUP,TAO,KMNO,TNSR,DRIFT,RAY,HYPE,LTC,FARTCOIN
```

### Settings Access

```python
from config.settings import settings

# Get all trading assets
assets = settings.TRADING_ASSETS
# ['BTC', 'ETH', 'SOL', ...]

# Backward compatibility - Drift still works
drift_assets = settings.DRIFT_ASSETS  # Same as TRADING_ASSETS
```

## 📊 Usage Across Modules

### 1. **Drift WebSocket**
```python
# ws/drift/client.py
from config.settings import settings

# Uses TRADING_ASSETS automatically
self.assets = settings.DRIFT_ASSETS[:settings.DRIFT_SUBSCRIBE_ASSETS]
```

### 2. **Binance OHLC**
```python
# Future: ws/binance/client.py
from config.settings import settings

# Will use TRADING_ASSETS
symbols = [f"{asset}USDT" for asset in settings.TRADING_ASSETS]
```

### 3. **CoinGecko Info**
```python
# main.py
from config.settings import settings

# Initialize coin info for all trading assets
symbols = settings.TRADING_ASSETS
await service.initialize_coins(symbols)
```

### 4. **API Endpoints**
```python
# api/routes.py
from config.settings import settings

# Get assets list
symbols = settings.TRADING_ASSETS
```

## 🔄 Integration with New WebSocket Sources

### Example: Adding Serum DEX

```python
# ws/serum/client.py
from config.settings import settings

class SerumWSClient:
    def __init__(self):
        # Automatically uses TRADING_ASSETS
        self.assets = settings.TRADING_ASSETS
        
    async def subscribe_all(self):
        for asset in self.assets:
            await self.subscribe(asset)
```

### Example: Adding Orca

```python
# ws/orca/client.py
from config.settings import settings

class OrcaWSClient:
    def __init__(self):
        # Automatically uses TRADING_ASSETS
        self.assets = settings.TRADING_ASSETS
        
    async def fetch_pools(self):
        pools = []
        for asset in self.assets:
            pool = await self.get_pool(asset)
            pools.append(pool)
        return pools
```

## 📈 Benefits

### 1. **Single Source of Truth**
- Define assets once, use everywhere
- No duplication
- Easy to maintain

### 2. **Easy Integration**
- New WS sources automatically use same assets
- No need to configure per source
- Consistent across all modules

### 3. **Centralized Management**
- Add/remove assets in one place
- All modules updated automatically
- No sync issues

### 4. **Backward Compatible**
- `DRIFT_ASSETS` still works (points to `TRADING_ASSETS`)
- Existing code doesn't break
- Smooth migration

## 🔧 How to Add/Remove Assets

### Add New Asset

```env
# .env
TRADING_ASSETS=BTC,ETH,SOL,NEW_ASSET
```

All modules will automatically:
- ✅ Subscribe to NEW_ASSET in Drift
- ✅ Fetch OHLC for NEW_ASSET from Binance
- ✅ Get coin info for NEW_ASSET from CoinGecko
- ✅ Show NEW_ASSET in API endpoints

### Remove Asset

```env
# .env
TRADING_ASSETS=BTC,ETH,SOL  # Removed DOGE
```

All modules will automatically:
- ✅ Stop subscribing to DOGE
- ✅ Stop fetching OHLC for DOGE
- ✅ Hide DOGE from API endpoints

## 📝 Migration Guide

### From DRIFT_ASSETS to TRADING_ASSETS

**Old Code:**
```python
from config.settings import settings

# Old way
assets = settings.DRIFT_ASSETS
```

**New Code:**
```python
from config.settings import settings

# New way (recommended)
assets = settings.TRADING_ASSETS

# Old way still works (backward compatible)
assets = settings.DRIFT_ASSETS  # Points to TRADING_ASSETS
```

### Update .env File

**Before:**
```env
DRIFT_ASSETS=BTC,ETH,SOL,...
```

**After:**
```env
TRADING_ASSETS=BTC,ETH,SOL,...
```

## 🎯 Use Cases

### 1. Multi-Exchange Support

```python
# Drift
drift_symbols = settings.TRADING_ASSETS

# Binance (add USDT suffix)
binance_symbols = [f"{asset}USDT" for asset in settings.TRADING_ASSETS]

# Serum (add /USDC suffix)
serum_symbols = [f"{asset}/USDC" for asset in settings.TRADING_ASSETS]
```

### 2. Unified Market Data

```python
from config.settings import settings

async def get_all_market_data():
    data = {}
    
    for asset in settings.TRADING_ASSETS:
        # Get from multiple sources
        drift_price = await drift_client.get_price(asset)
        binance_ohlc = await binance_client.get_ohlc(f"{asset}USDT")
        coingecko_info = await coingecko.get_info(asset)
        
        data[asset] = {
            "price": drift_price,
            "ohlc": binance_ohlc,
            "info": coingecko_info
        }
    
    return data
```

### 3. Dynamic Asset Management

```python
from config.settings import settings

# Get current assets
current_assets = settings.TRADING_ASSETS

# Filter by criteria
liquid_assets = [a for a in current_assets if is_liquid(a)]
defi_assets = [a for a in current_assets if is_defi(a)]

# Subscribe to filtered assets
for asset in liquid_assets:
    await subscribe(asset)
```

## 🔗 Related Configuration

```env
# Trading Assets (main config)
TRADING_ASSETS=BTC,ETH,SOL,...

# Drift specific
DRIFT_WS_URL=wss://drift-mainnet.rpc.drift.trade
DRIFT_SUBSCRIBE_ASSETS=25  # Max assets to subscribe

# Binance specific
BINANCE_API_URL=https://api.binance.com
BINANCE_WS_URL=wss://stream.binance.com:9443/ws
BINANCE_OHLC_INTERVAL=1h

# CoinGecko specific
# (uses TRADING_ASSETS automatically)
```

## ✅ Summary

**TRADING_ASSETS:**
- ✅ Single source of truth for all trading symbols
- ✅ Used by Drift, Binance, CoinGecko, API
- ✅ Easy to add/remove assets
- ✅ Backward compatible with DRIFT_ASSETS
- ✅ Ready for new WS integrations
- ✅ Centralized management
- ✅ No duplication

**Migration:**
- ✅ Change `DRIFT_ASSETS` to `TRADING_ASSETS` in .env
- ✅ Old code still works (backward compatible)
- ✅ New integrations use `TRADING_ASSETS`

---

**Last Updated**: 2026-04-14
**Version**: 1.0.0
