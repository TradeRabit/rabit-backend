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

### `GET /api/assets/search`

Searches tracked assets by symbol, name, or category.

Query params:

- `q`
- `limit`

Response model:

- `AssetSearchResponse`

### `GET /api/assets/categories`

Lists normalized categories currently represented by tracked assets.

Response model:

- `AssetCategoryListResponse`

Each category item includes:

- `name`
- `asset_count`

### `GET /api/assets/supported`

Returns the configured tracked asset symbols used by the backend.

Response model:

- `SupportedTradingAssetsResponse`

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

- The current asset universe is based on `settings.TRADING_ASSETS`.
- Search and category results only reflect assets the backend is already configured to track.
- OHLC can use Backpack or Binance depending on source selection and availability.
- `source=auto` uses configured backend behavior to pick the best available source.

## Related Documentation

- [Real-Time Market Data](../../features/market-data/index.md)
- [WebSocket and Market Data](../../websocket/index.md)
