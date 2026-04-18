"""Authenticated Backpack Exchange client for account, history, and execution tools."""
from __future__ import annotations

import base64
import binascii
import json
import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import aiohttp
from nacl.signing import SigningKey

from config.settings import settings


class BackpackClientError(RuntimeError):
    """Raised when Backpack request preparation or execution fails."""


def _normalize_value(value: Any) -> str:
    """Serialize a query/body scalar into Backpack's signing-safe string form."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    return str(value)


def _sorted_items(payload: Optional[Dict[str, Any]]) -> List[Tuple[str, str]]:
    """Convert payload into sorted key/value pairs, omitting None values."""
    if not payload:
        return []

    pairs: List[Tuple[str, str]] = []
    for key in sorted(payload):
        value = payload[key]
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            for item in value:
                if item is None:
                    continue
                pairs.append((key, _normalize_value(item)))
            continue
        pairs.append((key, _normalize_value(value)))
    return pairs


def _pairs_to_query(pairs: Sequence[Tuple[str, str]]) -> str:
    """Serialize key/value pairs into a stable query-string fragment."""
    return "&".join(f"{key}={value}" for key, value in pairs)


def _decode_signing_key(secret: str) -> SigningKey:
    """Best-effort decode of Backpack ED25519 signing secret."""
    raw = secret.strip()
    if not raw:
        raise BackpackClientError("Backpack API secret is not configured.")

    candidates: List[bytes] = []
    try:
        candidates.append(bytes.fromhex(raw))
    except ValueError:
        pass

    for decode_fn in (base64.b64decode, base64.urlsafe_b64decode):
        try:
            padded = raw + "=" * ((4 - len(raw) % 4) % 4)
            candidates.append(decode_fn(padded))
        except (binascii.Error, ValueError):
            continue

    candidates.append(raw.encode("utf-8"))

    for candidate in candidates:
        if len(candidate) == 32:
            return SigningKey(candidate)
        if len(candidate) == 64:
            return SigningKey(candidate[:32])

    raise BackpackClientError(
        "Backpack API secret must decode to a 32-byte or 64-byte ED25519 key."
    )


class BackpackClient:
    """Minimal Backpack API client using signed REST requests."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        recv_window_ms: int = 5000,
    ) -> None:
        self.api_url = (api_url or settings.BACKPACK_API_URL).rstrip("/")
        self.api_key = (api_key if api_key is not None else settings.BACKPACK_API_KEY).strip()
        self.api_secret = (
            api_secret if api_secret is not None else settings.BACKPACK_API_SECRET
        ).strip()
        self.recv_window_ms = recv_window_ms
        self._signing_key: Optional[SigningKey] = None

    def ensure_credentials(self) -> None:
        """Validate that Backpack credentials exist before private requests."""
        if not self.api_key:
            raise BackpackClientError("Backpack API key is not configured.")
        if not self.api_secret:
            raise BackpackClientError("Backpack API secret is not configured.")

    def _get_signing_key(self) -> SigningKey:
        """Load and cache the ED25519 signing key."""
        self.ensure_credentials()
        if self._signing_key is None:
            self._signing_key = _decode_signing_key(self.api_secret)
        return self._signing_key

    def _sign_message(self, message: str) -> str:
        """Return base64-encoded ED25519 signature for a request."""
        signature = self._get_signing_key().sign(message.encode("utf-8")).signature
        return base64.b64encode(signature).decode("utf-8")

    def _build_signing_message(
        self,
        instruction: str,
        timestamp_ms: int,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, Any]] = None,
        batch_orders: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> str:
        """Build the canonical signing string expected by Backpack."""
        if batch_orders is not None:
            segments: List[str] = []
            for order in batch_orders:
                order_pairs = [("instruction", instruction)] + _sorted_items(order)
                segments.append(_pairs_to_query(order_pairs))
            segments.append(f"timestamp={timestamp_ms}")
            segments.append(f"window={self.recv_window_ms}")
            return "&".join(segment for segment in segments if segment)

        payload_pairs = [("instruction", instruction)]
        payload_pairs.extend(_sorted_items(body or query))
        payload_pairs.append(("timestamp", str(timestamp_ms)))
        payload_pairs.append(("window", str(self.recv_window_ms)))
        return _pairs_to_query(payload_pairs)

    async def _request(
        self,
        method: str,
        path: str,
        instruction: str,
        *,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        batch_orders: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> Any:
        """Execute a signed Backpack request and return parsed JSON."""
        self.ensure_credentials()

        timestamp_ms = int(time.time() * 1000)
        message = self._build_signing_message(
            instruction,
            timestamp_ms,
            body=body,
            query=query,
            batch_orders=batch_orders,
        )
        headers = {
            "X-API-Key": self.api_key,
            "X-Signature": self._sign_message(message),
            "X-Timestamp": str(timestamp_ms),
            "X-Window": str(self.recv_window_ms),
        }
        if body is not None or batch_orders is not None:
            headers["Content-Type"] = "application/json"

        url = f"{self.api_url}{path}"
        params = {k: v for k, v in (query or {}).items() if v is not None}
        payload: Optional[Any] = None
        if batch_orders is not None:
            payload = list(batch_orders)
        elif body is not None:
            payload = body

        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(
                method.upper(),
                url,
                headers=headers,
                params=params or None,
                json=payload,
            ) as response:
                text = await response.text()
                try:
                    data = json.loads(text) if text else {}
                except json.JSONDecodeError:
                    data = {"raw": text}

                if response.status >= 400:
                    raise BackpackClientError(
                        f"Backpack API error ({response.status}): {data}"
                    )
                return data

    async def get_balances(self) -> Any:
        """Return account balances and locked funds."""
        return await self._request(
            "GET",
            "/api/v1/capital",
            "balanceQuery",
        )

    async def get_collateral(self, *, subaccount_id: Optional[int] = None) -> Any:
        """Return account collateral summary."""
        return await self._request(
            "GET",
            "/api/v1/capital/collateral",
            "collateralQuery",
            query={"subaccountId": subaccount_id},
        )

    async def get_open_orders(
        self,
        *,
        symbol: Optional[str] = None,
        market_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Any:
        """Return live open orders."""
        return await self._request(
            "GET",
            "/api/v1/orders",
            "orderQueryAll",
            query={
                "symbol": symbol,
                "marketType": market_type,
                "limit": limit,
            },
        )

    async def get_order_history(
        self,
        *,
        symbol: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """Return historical orders."""
        return await self._request(
            "GET",
            "/wapi/v1/history/orders",
            "orderHistoryQueryAll",
            query={
                "symbol": symbol,
                "limit": limit,
                "offset": offset,
            },
        )

    async def get_fill_history(
        self,
        *,
        symbol: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """Return historical fills."""
        return await self._request(
            "GET",
            "/wapi/v1/history/fills",
            "fillHistoryQueryAll",
            query={
                "symbol": symbol,
                "limit": limit,
                "offset": offset,
            },
        )

    async def get_positions(
        self,
        *,
        symbol: Optional[str] = None,
        market_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Any:
        """Return current positions."""
        return await self._request(
            "GET",
            "/api/v1/position",
            "positionQuery",
            query={
                "symbol": symbol,
                "marketType": market_type,
                "limit": limit,
            },
        )

    async def get_position_history(
        self,
        *,
        symbol: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """Return historical position snapshots."""
        return await self._request(
            "GET",
            "/wapi/v1/history/positions",
            "positionHistoryQueryAll",
            query={
                "symbol": symbol,
                "limit": limit,
                "offset": offset,
            },
        )

    async def place_order(
        self,
        *,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: Optional[str] = None,
        time_in_force: Optional[str] = None,
        post_only: Optional[bool] = None,
        reduce_only: Optional[bool] = None,
        client_id: Optional[str] = None,
        self_trade_prevention: Optional[str] = None,
    ) -> Any:
        """Place one live order through the Backpack batch-execution endpoint."""
        payload: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "quantity": quantity,
            "price": price,
            "timeInForce": time_in_force,
            "postOnly": post_only,
            "reduceOnly": reduce_only,
            "clientId": client_id,
            "selfTradePrevention": self_trade_prevention,
        }
        return await self._request(
            "POST",
            "/api/v1/orders",
            "orderExecute",
            batch_orders=[payload],
        )

    async def cancel_order(
        self,
        *,
        order_id: Optional[str] = None,
        client_id: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> Any:
        """Cancel a live open order."""
        return await self._request(
            "DELETE",
            "/api/v1/order",
            "orderCancel",
            body={
                "orderId": order_id,
                "clientId": client_id,
                "symbol": symbol,
            },
        )


_backpack_client: Optional[BackpackClient] = None


def get_backpack_client() -> BackpackClient:
    """Return a lazily constructed Backpack client."""
    global _backpack_client
    if _backpack_client is None:
        _backpack_client = BackpackClient()
    return _backpack_client
