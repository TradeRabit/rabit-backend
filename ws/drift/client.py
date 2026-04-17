"""Drift market data client using official public Drift endpoints."""
import asyncio
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import aiohttp
import websockets

from config.settings import settings
from utils.logger import get_logger
from ws.models import OHLCData, PriceUpdate

logger = get_logger(__name__)


class DriftWSClient:
    """
    Drift public market data client.

    Drift currently exposes public market data through multiple official feeds:
    - Data API websocket for candle subscriptions
    - DLOB websocket for live orderbook / trade streams

    The app listens to both so it can keep streaming even if one upstream feed is
    sparse or temporarily quiet.
    """

    STATS_URL = "https://data.api.drift.trade/stats/markets"

    def __init__(self):
        self.candle_url = settings.DRIFT_WS_URL
        self.dlob_url = settings.DRIFT_DLOB_WS_URL
        self.assets = settings.TRADING_ASSETS[:settings.DRIFT_SUBSCRIBE_ASSETS]
        self.connected = False
        self.candle_websocket = None
        self.dlob_websocket = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.callbacks: Dict[str, List[Callable]] = {}
        self.ohlc_callbacks: Dict[str, List[Callable]] = {}
        self.subscriptions: Dict[str, bool] = {}
        self._listen_tasks: List[asyncio.Task] = []
        self._stats_task: Optional[asyncio.Task] = None

    async def connect(self):
        """Connect to official Drift public feeds."""
        errors: List[str] = []

        self.candle_websocket, candle_error = await self._connect_socket(
            "Drift candle",
            self.candle_url,
            self._listen_candle,
        )
        if candle_error:
            errors.append(candle_error)

        self.dlob_websocket, dlob_error = await self._connect_socket(
            "Drift DLOB",
            self.dlob_url,
            self._listen_dlob,
        )
        if dlob_error:
            errors.append(dlob_error)

        self.connected = bool(self.candle_websocket or self.dlob_websocket)
        if not self.connected:
            raise RuntimeError("; ".join(errors) or "Unable to connect to Drift public feeds")

        self._stats_task = asyncio.create_task(self._poll_market_stats())
        logger.info(
            "Connected to Drift public feeds (candle=%s, dlob=%s)",
            bool(self.candle_websocket),
            bool(self.dlob_websocket),
        )

    async def disconnect(self):
        """Disconnect from Drift sockets and stop background tasks."""
        try:
            for task in self._listen_tasks:
                task.cancel()
            if self._stats_task:
                self._stats_task.cancel()

            for task in [*self._listen_tasks, self._stats_task]:
                if task:
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            for websocket in (self.candle_websocket, self.dlob_websocket):
                if websocket:
                    await websocket.close()

            if self.session and not self.session.closed:
                await self.session.close()

            self.connected = False
            logger.info("Disconnected from Drift public feeds")
        except Exception as e:
            logger.error(f"Error disconnecting: {str(e)}")

    async def subscribe(self, symbol: str, callback: Callable, subscribe_ohlc: bool = True):
        """Subscribe to Drift market data for a symbol."""
        base_symbol = self._normalize_symbol(symbol)
        market_symbol = f"{base_symbol}-PERP"

        if base_symbol not in self.callbacks:
            self.callbacks[base_symbol] = []
        self.callbacks[base_symbol].append(callback)

        if subscribe_ohlc and base_symbol not in self.ohlc_callbacks:
            self.ohlc_callbacks[base_symbol] = []

        if self.subscriptions.get(base_symbol, False):
            return

        await self._send_candle_subscription(market_symbol)
        await self._send_dlob_subscriptions(market_symbol)
        self.subscriptions[base_symbol] = True
        logger.info("Subscribed to %s on Drift public feeds", market_symbol)

    def subscribe_ohlc(self, symbol: str, callback: Callable):
        """Register OHLC updates for a symbol."""
        base_symbol = self._normalize_symbol(symbol)

        if base_symbol not in self.ohlc_callbacks:
            self.ohlc_callbacks[base_symbol] = []

        self.ohlc_callbacks[base_symbol].append(callback)
        logger.info(f"Registered OHLC callback for {base_symbol}")

    async def unsubscribe(self, symbol: str):
        """Unsubscribe from a symbol."""
        base_symbol = self._normalize_symbol(symbol)
        market_symbol = f"{base_symbol}-PERP"

        if base_symbol in self.subscriptions:
            await self._send_candle_unsubscription(market_symbol)
            await self._send_dlob_unsubscriptions(market_symbol)
            del self.subscriptions[base_symbol]
            self.callbacks.pop(base_symbol, None)
            self.ohlc_callbacks.pop(base_symbol, None)
            logger.info("Unsubscribed from %s", market_symbol)

    async def _connect_socket(self, label: str, url: str, listener: Callable):
        try:
            logger.info("Connecting to %s WebSocket: %s", label, url)
            websocket = await websockets.connect(url, ping_interval=20, ping_timeout=20)
            self._listen_tasks.append(asyncio.create_task(listener(websocket)))
            logger.info("Connected to %s WebSocket", label)
            return websocket, None
        except Exception as e:
            message = f"{label} connect failed: {e}"
            logger.warning(message)
            return None, message

    async def _send_json(self, websocket, payload: Dict[str, Any], label: str):
        if not websocket:
            return
        try:
            await websocket.send(json.dumps(payload))
        except Exception as e:
            logger.error("Error sending %s payload %s: %s", label, payload, e)

    async def _send_candle_subscription(self, market_symbol: str):
        await self._send_json(
            self.candle_websocket,
            {"type": "subscribe", "symbol": market_symbol, "resolution": "1"},
            "Drift candle subscribe",
        )

    async def _send_candle_unsubscription(self, market_symbol: str):
        await self._send_json(
            self.candle_websocket,
            {"type": "unsubscribe", "symbol": market_symbol, "resolution": "1"},
            "Drift candle unsubscribe",
        )

    async def _send_dlob_subscriptions(self, market_symbol: str):
        messages = [
            {
                "type": "subscribe",
                "channel": "trades",
                "marketType": "perp",
                "market": market_symbol,
            },
            {
                "type": "subscribe",
                "channel": "orderbook",
                "marketType": "perp",
                "market": market_symbol,
                "grouping": 10,
                "includeVamm": True,
                "includeIndicative": True,
            },
        ]
        for message in messages:
            await self._send_json(self.dlob_websocket, message, "Drift DLOB subscribe")

    async def _send_dlob_unsubscriptions(self, market_symbol: str):
        messages = [
            {
                "type": "unsubscribe",
                "channel": "trades",
                "marketType": "perp",
                "market": market_symbol,
            },
            {
                "type": "unsubscribe",
                "channel": "orderbook",
                "marketType": "perp",
                "market": market_symbol,
            },
        ]
        for message in messages:
            await self._send_json(self.dlob_websocket, message, "Drift DLOB unsubscribe")

    async def _listen_candle(self, websocket):
        await self._listen_socket(websocket, self._handle_candle_message, "candle")

    async def _listen_dlob(self, websocket):
        await self._listen_socket(websocket, self._handle_dlob_message, "dlob")

    async def _listen_socket(self, websocket, handler: Callable, label: str):
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await handler(data)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received from Drift %s feed: %s", label, message)
                except Exception as e:
                    logger.error("Error handling Drift %s message: %s", label, e)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Drift %s WebSocket connection closed", label)
            self._refresh_connected_state()
        except asyncio.CancelledError:
            logger.info("Drift %s listen task cancelled", label)
            raise
        except Exception as e:
            logger.error("Error in Drift %s listen loop: %s", label, e)
            self._refresh_connected_state()

    async def _handle_candle_message(self, data: Dict[str, Any]):
        msg_type = data.get("type")
        if msg_type == "subscription":
            logger.debug(f"Drift candle subscription confirmation: {data}")
            return

        if data.get("channel") == "heartbeat":
            logger.debug("Received Drift candle heartbeat")
            return

        symbol = self._normalize_symbol(data.get("symbol") or data.get("market") or data.get("channel"))
        if not symbol or not self._looks_like_candle(data):
            return

        price_update = self._price_from_candle(symbol, data)
        await self._emit_price(symbol, price_update)

        ohlc_data, interval = self._ohlc_from_candle(symbol, data)
        await self._emit_ohlc(symbol, ohlc_data, interval)

    async def _handle_message(self, data: Dict[str, Any]):
        """Backward-compatible alias used by existing tests and callers."""
        await self._handle_candle_message(data)

    async def _handle_dlob_message(self, data: Dict[str, Any]):
        if data.get("channel") == "heartbeat":
            logger.debug("Received Drift DLOB heartbeat")
            return

        if data.get("message"):
            logger.debug(f"Drift DLOB control message: {data}")
            return

        symbol = self._normalize_symbol(data.get("market") or data.get("symbol") or data.get("channel"))
        if not symbol:
            return

        channel = str(data.get("channel", "")).lower()
        if "trade" in channel:
            price = self._extract_trade_price(data)
            if price is not None:
                await self._emit_price(symbol, PriceUpdate(symbol=symbol, price=price))
            return

        if "orderbook" in channel:
            price = self._extract_mid_price(data)
            if price is not None:
                await self._emit_price(symbol, PriceUpdate(symbol=symbol, price=price))

    async def _emit_price(self, symbol: str, price_update: PriceUpdate):
        if symbol not in self.callbacks:
            return

        for callback in self.callbacks[symbol]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(price_update)
                else:
                    callback(price_update)
            except Exception as e:
                logger.error(f"Error in callback: {str(e)}")

    async def _emit_ohlc(self, symbol: str, ohlc_data: OHLCData, interval: str):
        if symbol not in self.ohlc_callbacks:
            return

        for callback in self.ohlc_callbacks[symbol]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    import inspect

                    sig = inspect.signature(callback)
                    if len(sig.parameters) >= 2:
                        await callback(ohlc_data, interval)
                    else:
                        await callback(ohlc_data)
                else:
                    callback(ohlc_data)
            except Exception as e:
                logger.error(f"Error in OHLC callback: {str(e)}")

    @staticmethod
    def _normalize_symbol(raw_symbol: Optional[str]) -> str:
        if not raw_symbol:
            return ""
        return raw_symbol.split(":")[-1].split("-")[0].split("_")[0].upper()

    @staticmethod
    def _looks_like_candle(data: Dict[str, Any]) -> bool:
        return any(key in data for key in ("close", "c", "open", "o", "high", "h", "low", "l"))

    @staticmethod
    def _parse_float(data: Dict[str, Any], *keys: str) -> float:
        for key in keys:
            value = data.get(key)
            if value is not None:
                return float(value)
        return 0.0

    @staticmethod
    def _parse_timestamp_ms(value: Any) -> int:
        if value is None:
            return 0

        if isinstance(value, (int, float)):
            value = int(value)
            return value // 1000 if value > 10**12 else value

        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return 0
            if stripped.isdigit():
                parsed = int(stripped)
                return parsed // 1000 if parsed > 10**12 else parsed
            try:
                dt = datetime.fromisoformat(stripped.replace("Z", "+00:00"))
                return int(dt.timestamp() * 1000)
            except ValueError:
                return 0

        return 0

    def _price_from_candle(self, symbol: str, data: Dict[str, Any]) -> PriceUpdate:
        return PriceUpdate(
            symbol=symbol,
            price=self._parse_float(data, "close", "c"),
            volume_24h=None,
            open_interest=None,
            funding_rate=None,
            high_24h=self._parse_float(data, "high", "h"),
            low_24h=self._parse_float(data, "low", "l"),
        )

    def _ohlc_from_candle(self, symbol: str, data: Dict[str, Any]) -> tuple[OHLCData, str]:
        interval = str(data.get("resolution") or data.get("i") or "1m")
        timestamp = self._parse_timestamp_ms(data.get("startTime") or data.get("t") or data.get("timestamp"))

        ohlc = OHLCData(
            symbol=symbol,
            timestamp=timestamp,
            open=self._parse_float(data, "open", "o"),
            high=self._parse_float(data, "high", "h"),
            low=self._parse_float(data, "low", "l"),
            close=self._parse_float(data, "close", "c"),
            volume=self._parse_float(data, "volume", "v"),
        )
        return ohlc, interval

    @classmethod
    def _extract_trade_price(cls, data: Dict[str, Any]) -> Optional[float]:
        payload = data.get("data") or data.get("trades") or data
        if isinstance(payload, list):
            for item in reversed(payload):
                price = cls._extract_scalar_price(item)
                if price is not None:
                    return price
            return None
        if isinstance(payload, dict):
            return cls._extract_scalar_price(payload)
        return None

    @classmethod
    def _extract_mid_price(cls, data: Dict[str, Any]) -> Optional[float]:
        payload = data.get("data") if isinstance(data.get("data"), dict) else data
        bids = payload.get("bids") or []
        asks = payload.get("asks") or []
        best_bid = cls._extract_book_price(bids)
        best_ask = cls._extract_book_price(asks)

        if best_bid is not None and best_ask is not None:
            return (best_bid + best_ask) / 2
        return best_bid if best_bid is not None else best_ask

    @staticmethod
    def _extract_scalar_price(payload: Any) -> Optional[float]:
        if isinstance(payload, dict):
            for key in ("price", "fillPrice", "oraclePrice", "markPrice", "p"):
                value = payload.get(key)
                if value is not None:
                    return float(value)
        if isinstance(payload, (list, tuple)) and payload:
            try:
                return float(payload[0])
            except (TypeError, ValueError):
                return None
        return None

    @classmethod
    def _extract_book_price(cls, side: List[Any]) -> Optional[float]:
        if not side:
            return None
        return cls._extract_scalar_price(side[0])

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def _poll_market_stats(self):
        """
        Keep a lightweight public HTTP fallback enabled.

        This endpoint is sometimes empty, but when it is populated it gives us
        oracle-style prices even if websocket traffic is sparse.
        """
        try:
            while True:
                try:
                    await self._ensure_session()
                    async with self.session.get(self.STATS_URL, timeout=aiohttp.ClientTimeout(total=20)) as response:
                        if response.status != 200:
                            logger.warning(f"Drift stats HTTP returned {response.status}")
                        else:
                            payload = await response.json()
                            markets = payload.get("markets", []) if isinstance(payload, dict) else payload
                            if markets:
                                await self._handle_market_stats(markets)
                            else:
                                logger.debug("Drift stats endpoint returned no markets")
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.warning(f"Drift stats polling error: {e}")

                await asyncio.sleep(15)
        except asyncio.CancelledError:
            logger.info("Drift stats polling cancelled")
            raise

    async def _handle_market_stats(self, markets: List[Dict[str, Any]]):
        market_map = {
            item.get("symbol", "").split("-")[0].upper(): item
            for item in markets
            if item.get("symbol", "").endswith("-PERP")
        }

        for symbol in list(self.subscriptions.keys()):
            item = market_map.get(symbol)
            if not item:
                continue

            price_update = PriceUpdate(
                symbol=symbol,
                price=float(item.get("oraclePrice", 0) or 0),
                volume_24h=float(item.get("volume24h", 0) or 0),
                open_interest=float(item.get("openInterest", 0) or 0),
                funding_rate=float(item.get("fundingRate", 0) or 0),
            )
            await self._emit_price(symbol, price_update)

    def _refresh_connected_state(self):
        sockets = [self.candle_websocket, self.dlob_websocket]
        self.connected = any(socket and not socket.closed for socket in sockets)

    def get_subscribed_symbols(self) -> List[str]:
        """Get list of subscribed symbols."""
        return list(self.subscriptions.keys())

    def is_subscribed(self, symbol: str) -> bool:
        """Check if symbol is subscribed."""
        base_symbol = self._normalize_symbol(symbol)
        return self.subscriptions.get(base_symbol, False)
