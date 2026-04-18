"""Read-only Drift account client.

Classification:
- purpose: authenticated wallet-linked private account reads
- scope: subaccount snapshot, balances, collateral, open orders, positions, and recent account history
- non-goals: live execution, signer custody, delegated signing
"""
from __future__ import annotations

from dataclasses import is_dataclass
from contextlib import suppress
from typing import Any, Callable, Dict, List, Sequence

from config.settings import settings


class DriftAccountReadOnlyClient:
    """Optional-dependency client for authenticated Drift account reads."""

    DEFAULT_HISTORY_LIMIT = 20
    MAX_HISTORY_LIMIT = 100
    MAX_SIGNATURE_SCAN = 250

    @staticmethod
    def _normalize_sdk_error(exc: Exception) -> Exception:
        message = str(exc)
        lowered = message.lower()
        if "too many requests" in lowered or "429" in lowered:
            return ValueError(
                "Drift read-only tools hit Solana RPC rate limits. "
                "Set DRIFT_RPC_URL to a dedicated RPC endpoint for reliable account and history reads."
            )
        return exc

    @staticmethod
    def _load_sdk():
        try:
            from anchorpy import Wallet
            from driftpy.addresses import get_user_account_public_key
            from driftpy.drift_client import DriftClient
            from driftpy.events.parse import parse_logs
            from driftpy.user_map.user_map import PollingConfig, UserMap, UserMapConfig
            from solders.keypair import Keypair
            from solders.pubkey import Pubkey
            from solana.rpc.async_api import AsyncClient
        except ImportError as exc:
            raise ValueError(
                "Drift private read-only tools require optional dependencies: "
                "driftpy, anchorpy, solders, and solana. Install them before using Drift account tools."
            ) from exc

        return {
            "Wallet": Wallet,
            "get_user_account_public_key": get_user_account_public_key,
            "DriftClient": DriftClient,
            "parse_logs": parse_logs,
            "PollingConfig": PollingConfig,
            "UserMap": UserMap,
            "UserMapConfig": UserMapConfig,
            "Keypair": Keypair,
            "Pubkey": Pubkey,
            "AsyncClient": AsyncClient,
        }

    @staticmethod
    def _serialize_scalar(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (bool, int, float, str)):
            return value

        for attr in ("to_string", "__int__", "__str__"):
            if hasattr(value, attr):
                try:
                    if attr == "to_string":
                        return value.to_string()
                    if attr == "__int__":
                        return int(value)
                    return str(value)
                except Exception:
                    continue
        return str(value)

    def _serialize_value(self, value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (list, tuple, set)):
            return [self._serialize_value(item) for item in value]
        if isinstance(value, dict):
            return {str(key): self._serialize_value(item) for key, item in value.items()}
        if is_dataclass(value):
            result: Dict[str, Any] = {}
            for field_name in value.__dataclass_fields__:  # type: ignore[attr-defined]
                result[field_name] = self._serialize_value(getattr(value, field_name))
            return result
        annotations = getattr(value.__class__, "__annotations__", None)
        if annotations:
            return {
                field_name: self._serialize_value(getattr(value, field_name, None))
                for field_name in annotations
            }
        if hasattr(value, "__dict__"):
            return {
                str(key): self._serialize_value(item)
                for key, item in vars(value).items()
                if not key.startswith("_")
            }
        return self._serialize_scalar(value)

    def _serialize_order(self, order: Any) -> Dict[str, Any]:
        return {
            "order_id": self._serialize_scalar(getattr(order, "order_id", None)),
            "user_order_id": self._serialize_scalar(getattr(order, "user_order_id", None)),
            "market_index": self._serialize_scalar(getattr(order, "market_index", None)),
            "market_type": self._serialize_scalar(getattr(order, "market_type", None)),
            "status": self._serialize_scalar(getattr(order, "status", None)),
            "order_type": self._serialize_scalar(getattr(order, "order_type", None)),
            "direction": self._serialize_scalar(getattr(order, "direction", None)),
            "price": self._serialize_scalar(getattr(order, "price", None)),
            "base_asset_amount": self._serialize_scalar(getattr(order, "base_asset_amount", None)),
            "base_asset_amount_filled": self._serialize_scalar(
                getattr(order, "base_asset_amount_filled", None)
            ),
            "quote_asset_amount_filled": self._serialize_scalar(
                getattr(order, "quote_asset_amount_filled", None)
            ),
            "reduce_only": getattr(order, "reduce_only", None),
            "post_only": getattr(order, "post_only", None),
            "immediate_or_cancel": getattr(order, "immediate_or_cancel", None),
            "trigger_price": self._serialize_scalar(getattr(order, "trigger_price", None)),
        }

    def _serialize_perp_position(self, position: Any) -> Dict[str, Any]:
        return {
            "market_index": self._serialize_scalar(getattr(position, "market_index", None)),
            "base_asset_amount": self._serialize_scalar(getattr(position, "base_asset_amount", None)),
            "quote_asset_amount": self._serialize_scalar(getattr(position, "quote_asset_amount", None)),
            "quote_entry_amount": self._serialize_scalar(getattr(position, "quote_entry_amount", None)),
            "open_bids": self._serialize_scalar(getattr(position, "open_bids", None)),
            "open_asks": self._serialize_scalar(getattr(position, "open_asks", None)),
            "lp_shares": self._serialize_scalar(getattr(position, "lp_shares", None)),
            "remainder_base_asset_amount": self._serialize_scalar(
                getattr(position, "remainder_base_asset_amount", None)
            ),
            "last_cumulative_funding_rate": self._serialize_scalar(
                getattr(position, "last_cumulative_funding_rate", None)
            ),
        }

    def _serialize_spot_position(self, position: Any) -> Dict[str, Any]:
        return {
            "market_index": self._serialize_scalar(getattr(position, "market_index", None)),
            "balance_type": self._serialize_scalar(getattr(position, "balance_type", None)),
            "scaled_balance": self._serialize_scalar(getattr(position, "scaled_balance", None)),
            "open_bids": self._serialize_scalar(getattr(position, "open_bids", None)),
            "open_asks": self._serialize_scalar(getattr(position, "open_asks", None)),
            "open_orders": self._serialize_scalar(getattr(position, "open_orders", None)),
        }

    async def _load_user(self, wallet_address: str, sub_account_id: int):
        sdk = self._load_sdk()
        connection = sdk["AsyncClient"](settings.DRIFT_RPC_URL)
        wallet = sdk["Wallet"](sdk["Keypair"]())
        drift_client = sdk["DriftClient"](connection, wallet, "mainnet")
        user_map = None

        try:
            if hasattr(drift_client, "subscribe"):
                await drift_client.subscribe()

            user_map = sdk["UserMap"](
                sdk["UserMapConfig"](
                    drift_client,
                    sdk["PollingConfig"](10),
                    skip_initial_load=False,
                )
            )
            account_pubkey = sdk["get_user_account_public_key"](
                drift_client.program_id,
                sdk["Pubkey"].from_string(wallet_address),
                sub_account_id,
            )
            await user_map.add_pubkey(account_pubkey)
            user = await user_map.must_get(str(account_pubkey))
            return user, str(account_pubkey), drift_client, connection, user_map
        except Exception as exc:
            if user_map is not None and hasattr(user_map, "unsubscribe"):
                with suppress(Exception):
                    maybe = user_map.unsubscribe()
                    if hasattr(maybe, "__await__"):
                        await maybe
            if hasattr(drift_client, "unsubscribe"):
                with suppress(Exception):
                    await drift_client.unsubscribe()
            with suppress(Exception):
                await connection.close()
            raise self._normalize_sdk_error(exc) from exc

    async def _with_user(self, wallet_address: str, sub_account_id: int, callback):
        user, account_pubkey, drift_client, connection, user_map = await self._load_user(
            wallet_address=wallet_address,
            sub_account_id=sub_account_id,
        )
        try:
            return await callback(user, account_pubkey, drift_client, connection)
        finally:
            if user_map is not None and hasattr(user_map, "unsubscribe"):
                with suppress(Exception):
                    maybe = user_map.unsubscribe()
                    if hasattr(maybe, "__await__"):
                        await maybe
            if hasattr(drift_client, "unsubscribe"):
                with suppress(Exception):
                    await drift_client.unsubscribe()
            with suppress(Exception):
                await connection.close()

    async def get_open_orders(self, wallet_address: str, sub_account_id: int = 0) -> Dict[str, Any]:
        async def _callback(user, account_pubkey, _drift_client, _connection):
            open_orders = []
            if hasattr(user, "get_open_orders"):
                open_orders = [self._serialize_order(order) for order in user.get_open_orders()]
            return {
                "wallet_address": wallet_address,
                "sub_account_id": sub_account_id,
                "user_account_public_key": account_pubkey,
                "open_orders": open_orders,
                "count": len(open_orders),
            }

        return await self._with_user(wallet_address, sub_account_id, _callback)

    async def get_open_positions(self, wallet_address: str, sub_account_id: int = 0) -> Dict[str, Any]:
        async def _callback(user, account_pubkey, _drift_client, _connection):
            positions: List[Dict[str, Any]] = []
            get_active = getattr(user, "get_active_perp_positions", None)
            if callable(get_active):
                positions = [self._serialize_perp_position(pos) for pos in get_active()]
            else:
                user_account = user.get_user_account()
                for position in getattr(user_account, "perp_positions", []):
                    if self._serialize_scalar(getattr(position, "base_asset_amount", 0)) not in {0, "0"}:
                        positions.append(self._serialize_perp_position(position))

            return {
                "wallet_address": wallet_address,
                "sub_account_id": sub_account_id,
                "user_account_public_key": account_pubkey,
                "open_positions": positions,
                "count": len(positions),
            }

        return await self._with_user(wallet_address, sub_account_id, _callback)

    async def get_positions(self, wallet_address: str, sub_account_id: int = 0) -> Dict[str, Any]:
        """Return current open positions for one Drift subaccount."""
        return await self.get_open_positions(
            wallet_address=wallet_address,
            sub_account_id=sub_account_id,
        )

    async def get_account_snapshot(self, wallet_address: str, sub_account_id: int = 0) -> Dict[str, Any]:
        async def _callback(user, account_pubkey, _drift_client, _connection):
            user_account = user.get_user_account()
            open_orders = []
            if hasattr(user, "get_open_orders"):
                open_orders = [self._serialize_order(order) for order in user.get_open_orders()]

            get_active = getattr(user, "get_active_perp_positions", None)
            if callable(get_active):
                open_positions = [self._serialize_perp_position(pos) for pos in get_active()]
            else:
                open_positions = []
                for position in getattr(user_account, "perp_positions", []):
                    if self._serialize_scalar(getattr(position, "base_asset_amount", 0)) not in {0, "0"}:
                        open_positions.append(self._serialize_perp_position(position))

            spot_balances = [
                self._serialize_spot_position(position)
                for position in getattr(user_account, "spot_positions", [])
                if self._serialize_scalar(getattr(position, "scaled_balance", 0)) not in {0, "0"}
            ]

            total_collateral = None
            free_collateral = None
            leverage = None
            if hasattr(user, "get_total_collateral"):
                with suppress(Exception):
                    total_collateral = self._serialize_scalar(user.get_total_collateral())
            if hasattr(user, "get_free_collateral"):
                with suppress(Exception):
                    free_collateral = self._serialize_scalar(user.get_free_collateral())
            if hasattr(user, "get_leverage"):
                with suppress(Exception):
                    leverage = self._serialize_scalar(user.get_leverage())

            return {
                "wallet_address": wallet_address,
                "sub_account_id": sub_account_id,
                "user_account_public_key": account_pubkey,
                "authority": self._serialize_scalar(getattr(user_account, "authority", None)),
                "delegate": self._serialize_scalar(getattr(user_account, "delegate", None)),
                "status": self._serialize_scalar(getattr(user_account, "status", None)),
                "open_orders_count": len(open_orders),
                "open_positions_count": len(open_positions),
                "spot_balances_count": len(spot_balances),
                "open_orders": open_orders,
                "open_positions": open_positions,
                "spot_balances": spot_balances,
                "total_collateral": total_collateral,
                "free_collateral": free_collateral,
                "leverage": leverage,
            }

        return await self._with_user(wallet_address, sub_account_id, _callback)

    async def get_balances(self, wallet_address: str, sub_account_id: int = 0) -> Dict[str, Any]:
        """Return current non-zero spot balances for one Drift subaccount."""
        snapshot = await self.get_account_snapshot(
            wallet_address=wallet_address,
            sub_account_id=sub_account_id,
        )
        return {
            "wallet_address": snapshot["wallet_address"],
            "sub_account_id": snapshot["sub_account_id"],
            "user_account_public_key": snapshot["user_account_public_key"],
            "spot_balances": snapshot["spot_balances"],
            "count": snapshot["spot_balances_count"],
        }

    async def get_collateral(self, wallet_address: str, sub_account_id: int = 0) -> Dict[str, Any]:
        """Return collateral summary for one Drift subaccount."""
        snapshot = await self.get_account_snapshot(
            wallet_address=wallet_address,
            sub_account_id=sub_account_id,
        )
        return {
            "wallet_address": snapshot["wallet_address"],
            "sub_account_id": snapshot["sub_account_id"],
            "user_account_public_key": snapshot["user_account_public_key"],
            "total_collateral": snapshot["total_collateral"],
            "free_collateral": snapshot["free_collateral"],
            "leverage": snapshot["leverage"],
        }

    @staticmethod
    def _normalize_history_limit(limit: int | None) -> int:
        if limit is None:
            return DriftAccountReadOnlyClient.DEFAULT_HISTORY_LIMIT
        return max(1, min(int(limit), DriftAccountReadOnlyClient.MAX_HISTORY_LIMIT))

    @staticmethod
    def _normalize_history_offset(offset: int | None) -> int:
        if offset is None:
            return 0
        return max(0, int(offset))

    def _compute_signature_scan_limit(self, limit: int, offset: int) -> int:
        requested = max(limit + offset, 10)
        return min(requested, self.MAX_SIGNATURE_SCAN)

    async def _get_recent_signatures(self, connection: Any, account_pubkey: str, limit: int) -> Sequence[Any]:
        sdk = self._load_sdk()
        response = await connection.get_signatures_for_address(
            sdk["Pubkey"].from_string(account_pubkey),
            limit=limit,
        )
        return list(getattr(response, "value", []) or [])

    async def _parse_recent_events(
        self,
        *,
        account_pubkey: str,
        connection: Any,
        drift_client: Any,
        event_types: set[str],
        limit: int,
        offset: int,
        matcher: Callable[[str, Any, str], bool],
    ) -> Dict[str, Any]:
        sdk = self._load_sdk()
        parse_logs = sdk["parse_logs"]
        signatures = await self._get_recent_signatures(
            connection=connection,
            account_pubkey=account_pubkey,
            limit=self._compute_signature_scan_limit(limit, offset),
        )

        matched_events: List[Dict[str, Any]] = []
        for signature_info in signatures:
            if len(matched_events) >= limit + offset:
                break

            tx_signature = getattr(signature_info, "signature", None)
            if tx_signature is None:
                continue

            with suppress(Exception):
                tx_response = await connection.get_transaction(
                    tx_signature,
                    commitment="confirmed",
                    max_supported_transaction_version=0,
                )
                tx_value = getattr(tx_response, "value", None)
                if tx_value is None:
                    continue

                meta = getattr(tx_value.transaction, "meta", None)
                logs = getattr(meta, "log_messages", None) if meta else None
                if not logs:
                    continue

                for event_index, event in enumerate(parse_logs(drift_client.program, list(logs))):
                    event_name = str(getattr(event, "name", "")).strip()
                    if event_name not in event_types:
                        continue
                    event_data = getattr(event, "data", None)
                    if not matcher(event_name, event_data, account_pubkey):
                        continue
                    matched_events.append(
                        {
                            "tx_signature": str(tx_signature),
                            "slot": getattr(signature_info, "slot", None),
                            "block_time": getattr(signature_info, "block_time", None),
                            "event_index": event_index,
                            "event_type": event_name,
                            "data": self._serialize_value(event_data),
                        }
                    )
                    if len(matched_events) >= limit + offset:
                        break

        return {
            "user_account_public_key": account_pubkey,
            "scanned_signatures": len(signatures),
            "matched_total": len(matched_events),
            "offset": offset,
            "limit": limit,
        }, matched_events[offset : offset + limit]

    @staticmethod
    def _matches_user_field(event_data: Any, account_pubkey: str) -> bool:
        return str(getattr(event_data, "user", "")).strip() == account_pubkey

    @staticmethod
    def _matches_order_action(event_data: Any, account_pubkey: str) -> bool:
        maker = str(getattr(event_data, "maker", "") or "").strip()
        taker = str(getattr(event_data, "taker", "") or "").strip()
        return maker == account_pubkey or taker == account_pubkey

    async def get_order_history(
        self,
        wallet_address: str,
        sub_account_id: int = 0,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Dict[str, Any]:
        limit = self._normalize_history_limit(limit)
        offset = self._normalize_history_offset(offset)

        async def _callback(_user, account_pubkey, drift_client, connection):
            metadata, events = await self._parse_recent_events(
                account_pubkey=account_pubkey,
                connection=connection,
                drift_client=drift_client,
                event_types={"OrderRecord"},
                limit=limit,
                offset=offset,
                matcher=lambda _name, data, target: self._matches_user_field(data, target),
            )
            return {
                "wallet_address": wallet_address,
                "sub_account_id": sub_account_id,
                "order_history": events,
                "count": len(events),
                **metadata,
            }

        return await self._with_user(wallet_address, sub_account_id, _callback)

    async def get_fill_history(
        self,
        wallet_address: str,
        sub_account_id: int = 0,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Dict[str, Any]:
        limit = self._normalize_history_limit(limit)
        offset = self._normalize_history_offset(offset)

        async def _callback(_user, account_pubkey, drift_client, connection):
            metadata, events = await self._parse_recent_events(
                account_pubkey=account_pubkey,
                connection=connection,
                drift_client=drift_client,
                event_types={"OrderActionRecord"},
                limit=limit,
                offset=offset,
                matcher=lambda _name, data, target: self._matches_order_action(data, target)
                and (
                    getattr(data, "fill_record_id", None) is not None
                    or getattr(data, "base_asset_amount_filled", None) is not None
                    or getattr(data, "quote_asset_amount_filled", None) is not None
                ),
            )
            return {
                "wallet_address": wallet_address,
                "sub_account_id": sub_account_id,
                "fill_history": events,
                "count": len(events),
                **metadata,
            }

        return await self._with_user(wallet_address, sub_account_id, _callback)

    async def get_position_history(
        self,
        wallet_address: str,
        sub_account_id: int = 0,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Dict[str, Any]:
        limit = self._normalize_history_limit(limit)
        offset = self._normalize_history_offset(offset)

        def _matcher(event_name: str, event_data: Any, target: str) -> bool:
            if event_name in {"SettlePnlRecord", "FundingPaymentRecord", "LiquidationRecord"}:
                return self._matches_user_field(event_data, target)
            return False

        async def _callback(_user, account_pubkey, drift_client, connection):
            metadata, events = await self._parse_recent_events(
                account_pubkey=account_pubkey,
                connection=connection,
                drift_client=drift_client,
                event_types={"SettlePnlRecord", "FundingPaymentRecord", "LiquidationRecord"},
                limit=limit,
                offset=offset,
                matcher=_matcher,
            )
            return {
                "wallet_address": wallet_address,
                "sub_account_id": sub_account_id,
                "position_history": events,
                "count": len(events),
                **metadata,
            }

        return await self._with_user(wallet_address, sub_account_id, _callback)


_drift_account_client: DriftAccountReadOnlyClient | None = None


def get_drift_account_client() -> DriftAccountReadOnlyClient:
    """Return singleton Drift account read-only client."""
    global _drift_account_client
    if _drift_account_client is None:
        _drift_account_client = DriftAccountReadOnlyClient()
    return _drift_account_client


__all__ = ["DriftAccountReadOnlyClient", "get_drift_account_client"]
