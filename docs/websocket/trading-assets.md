# Trading Assets

This document describes the shared asset list used across market-data features.

## Current Configuration Source

The backend uses `TRADING_ASSETS` as the main source of configured symbols.

This list is used to coordinate:

- exchange subscriptions
- market-data services
- selected charting and enrichment flows

## Why It Exists

Using one shared asset list reduces drift between:

- exchange stream subscriptions
- chart history workflows
- metadata preloading

## Related Documentation

- [WebSocket Index](./index.md)
- [Data Sources](./data-sources.md)
- [Project Overview](../architecture/project/index.md)
