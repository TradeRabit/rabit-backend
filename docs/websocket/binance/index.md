# Binance Market Data

This section documents Binance as an OHLC and chart-oriented market-data source in the backend.

## Current Role

Binance is mainly used for:

- historical OHLC
- chart-oriented candle retrieval
- charting support and technical analysis inputs

## Visual Flow

```text
Binance OHLC source
  -> ws/binance/
  -> shared handlers and services
  -> candle storage or chart consumers
  -> frontend charts and analysis features
```

## What It Is Not

Binance is not currently documented here as a per-user exchange execution surface for the agent.

This page is about market data, not account ownership or execution auth.

## Related Code Areas

- `ws/binance/`
- `ws/services/`
- `ws/handlers/`

## Related Documentation

- [WebSocket Overview](../overview.md)
- [Trading Assets](../trading-assets.md)
- [Real-Time Market Data](../../features/market-data/index.md)
