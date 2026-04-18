# Data Sources

This document summarizes the main data sources used by the backend.

## Current Source Types

### Exchange Market Data

- Drift market streams
- Backpack market streams
- Binance for historical or chart-oriented OHLC workflows

### Metadata and Enrichment

- CoinGecko

### News and Research

- configured news sources
- web search when enabled

## Why This Matters

Different backend features depend on different data types:

- agent analysis depends on market and research sources
- charting depends on exchange and OHLC sources
- exchange-specific execution depends on account-aware provider integrations

## Related Documentation

- [WebSocket Index](./index.md)
- [Backpack WebSocket Docs](./backpack/index.md)
- [Drift WebSocket Docs](./drift/index.md)
- [Binance Market Data Docs](./binance/index.md)
- [Integrations Index](../integrations/index.md)
- [Real-Time Market Data](../features/market-data/index.md)
