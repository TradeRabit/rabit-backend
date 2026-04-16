# Price Monitor - Validation/Invalidation Alerts

## Overview

Price Monitor adalah sistem real-time monitoring untuk trade setups dengan validation dan invalidation price levels. Agent dapat set alert untuk mendapatkan notifikasi ketika price mencapai level validation (trade setup confirmed) atau invalidation (stop loss hit).

## Konsep

### Validation vs Invalidation

**Validation Price**: Level harga yang mengkonfirmasi trade setup bekerja dengan baik
- Untuk LONG: Price naik ke validation level = ✅ Trade valid
- Untuk SHORT: Price turun ke validation level = ✅ Trade valid

**Invalidation Price**: Level harga yang membatalkan trade setup (stop loss)
- Untuk LONG: Price turun ke invalidation level = ❌ Trade invalid
- Untuk SHORT: Price naik ke invalidation level = ❌ Trade invalid

### Trade Directions

#### LONG (Bullish Setup)
```
Validation Price:    $100,000  ← Price naik ke sini = VALID ✅
Current Price:       $95,000
Invalidation Price:  $90,000   ← Price turun ke sini = INVALID ❌
```

#### SHORT (Bearish Setup)
```
Invalidation Price:  $3,500    ← Price naik ke sini = INVALID ❌
Current Price:       $3,200
Validation Price:    $3,000    ← Price turun ke sini = VALID ✅
```

## Tools Available

### 1. `add_price_alert`
Tambah price alert untuk monitoring

**Parameters:**
- `symbol` (string, required): Trading symbol (BTC, ETH, SOL, etc.)
- `validation_price` (number, required): Price level untuk validation
- `invalidation_price` (number, required): Price level untuk invalidation
- `direction` (string, optional): "LONG" atau "SHORT" (default: "LONG")

**Example:**
```python
# LONG setup: BTC breaks above 100k (validation) or below 90k (invalidation)
result = await add_price_alert(
    symbol="BTC",
    validation_price=100000,
    invalidation_price=90000,
    direction="LONG"
)
```

## Use Cases

### Use Case 1: Breakout Trading
```python
await start_price_monitor()

await add_price_alert(
    symbol="BTC",
    validation_price=100000,  # Breakout confirmed
    invalidation_price=95000,  # Failed breakout
    direction="LONG"
)
```

## Architecture

```
Trading Agent → Price Monitor Tools → Price Monitor → CoinGecko Client
```

## Testing

Run tests:
```bash
cd rabit-backend
python test/price_monitor/test_price_monitor.py
```
