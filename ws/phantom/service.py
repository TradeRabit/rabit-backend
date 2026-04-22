"""Phantom market data service backed by Hyperliquid snapshots."""
from __future__ import annotations

import asyncio
from typing import Optional

import aiohttp

from config.settings import settings
from utils.logger import get_logger
from ws.models import PriceUpdate

logger = get_logger(__name__)


class PhantomMarketService:
    """Poll Hyperliquid asset contexts and expose them as Phantom market data."""

    def __init__(self) -> None:
        self.api_url = settings.HYPERLIQUID_API_URL.rstrip("/")
        self.dex = settings.HYPERLIQUID_DEX
        self.poll_interval_seconds = max(1.0, float(settings.PHANTOM_PRICE_POLL_INTERVAL_SECONDS))
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self.handler = None
        self._tracked_symbols = {asset.strip().upper() for asset in settings.TRADING_ASSETS if asset.strip()}
        self._spot_token_meta: dict[int, dict] = {}

    async def start(self, handler) -> None:
        """Start the polling loop."""
        if self._running:
            return
        self.handler = handler
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("Phantom market service started")

    async def stop(self) -> None:
        """Stop the polling loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Phantom market service stopped")

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                await self._refresh_spot_asset_contexts()
                await self._refresh_futures_asset_contexts()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error(f"Phantom market refresh failed: {exc}")
            await asyncio.sleep(self.poll_interval_seconds)

    async def _post_info(self, payload: dict):
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

    async def _refresh_futures_asset_contexts(self) -> None:
        payload = {"type": "metaAndAssetCtxs"}
        if self.dex:
            payload["dex"] = self.dex
        raw = await self._post_info(payload)

        if not isinstance(raw, list) or len(raw) < 2:
            raise RuntimeError("Unexpected Hyperliquid metaAndAssetCtxs response shape.")

        meta = raw[0] or {}
        asset_contexts = raw[1] or []
        universe = meta.get("universe") or []

        for market_meta, asset_ctx in zip(universe, asset_contexts):
            symbol = str(market_meta.get("name") or "").strip().upper()
            if not symbol:
                continue
            if symbol not in self._tracked_symbols:
                continue

            mark_price = asset_ctx.get("markPx") or asset_ctx.get("midPx")
            if mark_price is None:
                continue

            prev_day = asset_ctx.get("prevDayPx")
            change_24h = None
            try:
                prev_day_float = float(prev_day) if prev_day is not None else 0.0
                mark_price_float = float(mark_price)
                if prev_day_float > 0:
                    change_24h = ((mark_price_float - prev_day_float) / prev_day_float) * 100.0
            except Exception:
                change_24h = None

            update = PriceUpdate(
                symbol=symbol,
                price=float(mark_price),
                change_24h=change_24h,
                volume_24h=float(asset_ctx.get("dayNtlVlm") or 0.0),
                notional_volume_24h=float(asset_ctx.get("dayNtlVlm") or 0.0),
                base_volume_24h=None,
                open_interest=float(asset_ctx.get("openInterest") or 0.0),
                funding_rate=float(asset_ctx.get("funding") or 0.0),
                oracle_price=self._safe_float(asset_ctx.get("oraclePx")),
                premium=self._safe_float(asset_ctx.get("premium")),
                high_24h=None,
                low_24h=None,
                market_cap=None,
                fdv=None,
                circulating_supply=None,
                total_supply=None,
                max_leverage=self._safe_float(market_meta.get("maxLeverage")),
                only_isolated=bool(market_meta.get("onlyIsolated", False)),
                market_pair=symbol,
                full_name=symbol,
                token_index=None,
                is_canonical=None,
                source_exchange="phantom_futures",
            )
            await self.handler.on_price_update_from_exchange("phantom_futures", update)

    async def _refresh_spot_asset_contexts(self) -> None:
        raw = await self._post_info({"type": "spotMetaAndAssetCtxs"})
        if not isinstance(raw, list) or len(raw) < 2:
            raise RuntimeError("Unexpected Hyperliquid spotMetaAndAssetCtxs response shape.")

        meta = raw[0] or {}
        asset_contexts = raw[1] or []
        universe = meta.get("universe") or []
        tokens = meta.get("tokens") or []
        self._spot_token_meta = {
            int(token.get("index")): token
            for token in tokens
            if token.get("index") is not None
        }
        token_by_index = {
            int(token.get("index")): str(token.get("name") or "").strip().upper()
            for token in tokens
            if token.get("index") is not None
        }

        for pair_meta, asset_ctx in zip(universe, asset_contexts):
            token_indexes = pair_meta.get("tokens") or []
            if len(token_indexes) < 2:
                continue

            base_symbol = token_by_index.get(int(token_indexes[0]), "")
            quote_symbol = token_by_index.get(int(token_indexes[1]), "")
            if quote_symbol != "USDC":
                continue
            if base_symbol not in self._tracked_symbols:
                continue

            token_meta = self._spot_token_meta.get(int(token_indexes[0]), {})
            mark_price = asset_ctx.get("markPx") or asset_ctx.get("midPx") or asset_ctx.get("prevDayPx")
            if mark_price is None:
                continue

            change_24h = None
            try:
                prev_day_float = float(asset_ctx.get("prevDayPx") or 0.0)
                mark_price_float = float(mark_price)
                if prev_day_float > 0:
                    change_24h = ((mark_price_float - prev_day_float) / prev_day_float) * 100.0
            except Exception:
                change_24h = None

            price_float = float(mark_price)
            circulating_supply = self._safe_float(asset_ctx.get("circulatingSupply"))
            total_supply = self._safe_float(asset_ctx.get("totalSupply"))

            update = PriceUpdate(
                symbol=base_symbol,
                price=price_float,
                change_24h=change_24h,
                volume_24h=float(asset_ctx.get("dayNtlVlm") or 0.0),
                notional_volume_24h=float(asset_ctx.get("dayNtlVlm") or 0.0),
                base_volume_24h=self._safe_float(asset_ctx.get("dayBaseVlm")),
                open_interest=None,
                funding_rate=None,
                oracle_price=None,
                premium=None,
                high_24h=None,
                low_24h=None,
                market_cap=(price_float * circulating_supply) if circulating_supply is not None else None,
                fdv=(price_float * total_supply) if total_supply is not None else None,
                circulating_supply=circulating_supply,
                total_supply=total_supply,
                max_leverage=None,
                only_isolated=None,
                market_pair=str(pair_meta.get("name") or f"{base_symbol}/{quote_symbol}"),
                full_name=str(token_meta.get("fullName") or base_symbol),
                token_index=int(token_meta["index"]) if token_meta.get("index") is not None else None,
                is_canonical=bool(pair_meta.get("isCanonical", token_meta.get("isCanonical", False))),
                source_exchange="phantom_spot",
            )
            await self.handler.on_price_update_from_exchange("phantom_spot", update)

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        try:
            if value in (None, ""):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None


_phantom_service: Optional[PhantomMarketService] = None


def get_phantom_service() -> PhantomMarketService:
    """Return the Phantom market service singleton."""
    global _phantom_service
    if _phantom_service is None:
        _phantom_service = PhantomMarketService()
    return _phantom_service
