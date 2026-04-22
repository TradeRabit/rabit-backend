"""Hyperliquid historical candle downloader used by the Phantom market surface."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import aiohttp

from config.settings import settings
from utils.logger import get_logger
from ws.models import OHLCData

logger = get_logger(__name__)


class HyperliquidHistoryDownloader:
    """Download historical candle snapshots from Hyperliquid info API."""

    def __init__(self) -> None:
        self.api_url = settings.HYPERLIQUID_API_URL.rstrip("/")
        self.dex = settings.HYPERLIQUID_DEX
        self._spot_pair_cache: Dict[str, str] = {}

    async def download_history(
        self,
        *,
        symbol: str,
        interval: str,
        limit: int = 100,
        market_source: str = "phantom_futures",
    ) -> List[OHLCData]:
        """Return Hyperliquid candle snapshots for one symbol and interval."""
        normalized_symbol = str(symbol or "").strip().upper()
        clamped_limit = max(1, min(int(limit or 100), 5000))
        end_time = datetime.now(timezone.utc)
        start_time = end_time - self._estimate_window(interval=interval, limit=clamped_limit)
        coin = await self._resolve_coin_identifier(
            symbol=normalized_symbol,
            market_source=market_source,
        )

        payload = {
            "type": "candleSnapshot",
            "req": {
                "coin": coin,
                "interval": interval,
                "startTime": int(start_time.timestamp() * 1000),
                "endTime": int(end_time.timestamp() * 1000),
            },
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/info",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status != 200:
                        body = await response.text()
                        logger.error(
                            "Hyperliquid candle snapshot failed for %s %s: %s %s",
                            coin,
                            interval,
                            response.status,
                            body,
                        )
                        return []
                    raw = await response.json()
        except Exception as exc:
            logger.error(f"Error downloading Hyperliquid candles for {coin}: {exc}")
            return []

        candles: List[OHLCData] = []
        for item in raw[-clamped_limit:]:
            try:
                candles.append(
                    OHLCData(
                        symbol=normalized_symbol,
                        timestamp=int(item["t"]),
                        open=float(item["o"]),
                        high=float(item["h"]),
                        low=float(item["l"]),
                        close=float(item["c"]),
                        volume=float(item["v"]),
                        number_of_trades=int(item.get("n", 0)),
                    )
                )
            except Exception as exc:
                logger.warning(f"Skipping malformed Hyperliquid candle for {coin}: {exc}")
        return candles

    async def _resolve_coin_identifier(self, *, symbol: str, market_source: str) -> str:
        """Resolve the Hyperliquid candle coin identifier for spot or futures markets."""
        normalized_source = str(market_source or "phantom_futures").strip().lower()
        if normalized_source != "phantom_spot":
          return symbol

        cached = self._spot_pair_cache.get(symbol)
        if cached:
            return cached

        raw = await self._post_info({"type": "spotMetaAndAssetCtxs"})
        if not isinstance(raw, list) or len(raw) < 2:
            raise RuntimeError("Unexpected Hyperliquid spotMetaAndAssetCtxs response shape.")

        meta = raw[0] or {}
        universe = meta.get("universe") or []
        tokens = meta.get("tokens") or []
        token_by_index = {
            int(token.get("index")): str(token.get("name") or "").strip().upper()
            for token in tokens
            if token.get("index") is not None
        }

        for pair_meta in universe:
            token_indexes = pair_meta.get("tokens") or []
            if len(token_indexes) < 2:
                continue

            base_symbol = token_by_index.get(int(token_indexes[0]), "")
            quote_symbol = token_by_index.get(int(token_indexes[1]), "")
            if base_symbol == symbol and quote_symbol == "USDC":
                pair_name = str(pair_meta.get("name") or "").strip()
                if pair_name:
                    self._spot_pair_cache[symbol] = pair_name
                    return pair_name

        raise RuntimeError(f"Hyperliquid spot pair for symbol '{symbol}' was not found.")

    async def _post_info(self, payload: dict):
        """Post one info request to Hyperliquid."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/info",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    body = await response.text()
                    raise RuntimeError(
                        f"Hyperliquid info request failed with {response.status}: {body}"
                    )
                return await response.json()

    def _estimate_window(self, *, interval: str, limit: int) -> timedelta:
        mapping = {
            "1m": timedelta(minutes=1),
            "3m": timedelta(minutes=3),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "30m": timedelta(minutes=30),
            "1h": timedelta(hours=1),
            "2h": timedelta(hours=2),
            "4h": timedelta(hours=4),
            "8h": timedelta(hours=8),
            "12h": timedelta(hours=12),
            "1d": timedelta(days=1),
            "3d": timedelta(days=3),
            "1w": timedelta(days=7),
            "1M": timedelta(days=30),
        }
        return mapping.get(interval, timedelta(hours=1)) * limit
