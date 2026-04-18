# Assets and Chart Data API

This group covers market-facing asset lookup and OHLC retrieval.

## Endpoints

### `GET /api/assets`

Lists tracked assets with basic price information.

Query params:

- `category`
- `limit`

Response model:

- `AssetListResponse`

### `GET /api/assets/{symbol}`

Returns detailed information for one asset.

Path params:

- `symbol`

Response model:

- `AssetDetailResponse`

Main fields include:

- basic asset identity
- price and change
- volume and daily range when available
- market cap and other enrichment when available
- description, categories, and links

### `GET /api/assets/{symbol}/ohlc`

Returns OHLC chart data for one asset.

Path params:

- `symbol`

Query params:

- `interval`
- `limit`
- `source`

Response model:

- `OHLCResponse`

## Notes

- OHLC can use Backpack or Binance depending on source selection and availability.
- `source=auto` uses configured backend behavior to pick the best available source.

## Related Documentation

- [Real-Time Market Data](../../features/market-data/index.md)
- [WebSocket and Market Data](../../websocket/index.md)
