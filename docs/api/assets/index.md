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

### `GET /api/assets/categories/{category}`

Returns tracked assets belonging to one normalized category.

Path params:

- `category`

Query params:

- `limit`

Response model:

- `AssetCategoryAssetsResponse`

### `GET /api/assets/supported`

Returns the configured tracked asset symbols used by the backend.

Response model:

- `SupportedTradingAssetsResponse`

### `GET /api/assets/trending`

Returns a lightweight trending ranking built from tracked assets.

Query params:

- `limit`

Response model:

- `TrendingAssetsResponse`

Each item includes:

- `rank`
- `score`
- `volume_24h`
- `reasons`

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

### `GET /api/assets/{symbol}/summary`

Returns a one-shot summary payload for frontend detail headers and overview sections.

Path params:

- `symbol`

Query params:

- `related_limit`

Response model:

- `AssetSummaryResponse`

Summary payload includes:

- key market fields
- `primary_category`
- short metadata and links
- a small `related_assets` list

### `GET /api/assets/{symbol}/related`

Returns related tracked assets using shared categories.

Path params:

- `symbol`

Query params:

- `limit`

Response model:

- `RelatedAssetsResponse`

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
