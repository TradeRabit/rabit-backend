"""Drift transaction builder for same-wallet mobile signing.

Classification:
- purpose: build unsigned Drift execution payloads for mobile wallet signing
- scope: same-wallet perp order preparation only
- non-goals: backend-held signing, delegated signing, order submission
"""
from __future__ import annotations

import base64
from contextlib import suppress
from typing import Any, Dict, Optional

from config.settings import settings


class DriftTxBuilderWalletError(ValueError):
    """Raised when the authenticated wallet cannot be used for Drift tx building."""


class DriftTxBuilderValidationError(ValueError):
    """Raised when the requested Drift order intent is invalid."""


class DriftExecutionTxBuilder:
    """Build unsigned Drift transactions for same-wallet mobile signing."""

    @staticmethod
    def _load_sdk() -> Dict[str, Any]:
        try:
            from anchorpy import Wallet
            from driftpy.drift_client import DriftClient
            from driftpy.types import (
                MarketType,
                OrderParams,
                OrderParamsBitFlag,
                OrderType,
                PositionDirection,
                PostOnlyParams,
            )
            from solders.keypair import Keypair
            from solders.message import MessageV0, to_bytes_versioned
            from solders.null_signer import NullSigner
            from solders.pubkey import Pubkey
            from solders.transaction import VersionedTransaction
            from solana.rpc.async_api import AsyncClient
        except ImportError as exc:
            raise ValueError(
                "Building Drift execution payloads requires optional dependencies: "
                "driftpy, anchorpy, solders, and solana."
            ) from exc

        return {
            "Wallet": Wallet,
            "DriftClient": DriftClient,
            "MarketType": MarketType,
            "OrderParams": OrderParams,
            "OrderParamsBitFlag": OrderParamsBitFlag,
            "OrderType": OrderType,
            "PositionDirection": PositionDirection,
            "PostOnlyParams": PostOnlyParams,
            "Keypair": Keypair,
            "MessageV0": MessageV0,
            "NullSigner": NullSigner,
            "Pubkey": Pubkey,
            "VersionedTransaction": VersionedTransaction,
            "AsyncClient": AsyncClient,
            "to_bytes_versioned": to_bytes_versioned,
        }

    @staticmethod
    def _normalize_side(side: str, sdk: Dict[str, Any]):
        value = str(side or "").strip().lower()
        if value in {"buy", "long"}:
            return sdk["PositionDirection"].Long()
        if value in {"sell", "short"}:
            return sdk["PositionDirection"].Short()
        raise DriftTxBuilderValidationError(
            "Drift execution side must be one of: long, short, buy, sell."
        )

    @staticmethod
    def _normalize_order_type(order_type: str, sdk: Dict[str, Any]):
        value = str(order_type or "").strip().lower()
        mapping = {
            "limit": sdk["OrderType"].Limit(),
            "market": sdk["OrderType"].Market(),
            "trigger_limit": sdk["OrderType"].TriggerLimit(),
            "trigger_market": sdk["OrderType"].TriggerMarket(),
        }
        if value not in mapping:
            raise DriftTxBuilderValidationError(
                "Drift execution order_type must be one of: limit, market, trigger_limit, trigger_market."
            )
        return mapping[value], value

    @staticmethod
    def _parse_required_int(value: Any, field_name: str) -> int:
        try:
            parsed = int(str(value).strip())
        except Exception as exc:
            raise DriftTxBuilderValidationError(
                f"Drift execution field '{field_name}' must be an integer-like string."
            ) from exc
        if parsed < 0:
            raise DriftTxBuilderValidationError(
                f"Drift execution field '{field_name}' must be non-negative."
            )
        return parsed

    def _build_order_params(self, order_intent: Dict[str, Any], sdk: Dict[str, Any]):
        market_index = order_intent.get("market_index")
        if market_index is None:
            raise DriftTxBuilderValidationError(
                "Drift execution prepare requires market_index for v1 transaction building."
            )

        direction = self._normalize_side(order_intent.get("side"), sdk)
        order_type, order_type_name = self._normalize_order_type(order_intent.get("order_type"), sdk)
        base_asset_amount = self._parse_required_int(
            order_intent.get("base_asset_amount"),
            "base_asset_amount",
        )
        price = 0
        if order_intent.get("price") is not None:
            price = self._parse_required_int(order_intent.get("price"), "price")
        if order_type_name in {"limit", "trigger_limit"} and price <= 0:
            raise DriftTxBuilderValidationError(
                "Drift limit-style orders require a positive price."
            )

        bit_flags = 0
        if bool(order_intent.get("immediate_or_cancel")):
            bit_flags |= sdk["OrderParamsBitFlag"].IMMEDIATE_OR_CANCEL

        post_only = (
            sdk["PostOnlyParams"].TryPostOnly()
            if bool(order_intent.get("post_only"))
            else sdk["PostOnlyParams"].NONE()
        )

        client_order_id = order_intent.get("client_order_id")
        user_order_id = 0 if client_order_id is None else self._parse_required_int(
            client_order_id,
            "client_order_id",
        )

        return sdk["OrderParams"](
            order_type=order_type,
            base_asset_amount=base_asset_amount,
            market_index=int(market_index),
            direction=direction,
            market_type=sdk["MarketType"].Perp(),
            user_order_id=user_order_id,
            price=price,
            reduce_only=bool(order_intent.get("reduce_only")),
            post_only=post_only,
            bit_flags=bit_flags,
        )

    async def _build_single_ix_payload(
        self,
        *,
        wallet_address: str,
        sub_account_id: int,
        ix_builder,
        classification: str,
        action: str,
        market_type: str,
    ) -> Dict[str, Any]:
        """Build a generic unsigned single-instruction Drift transaction payload."""
        sdk = self._load_sdk()
        wallet_pubkey = sdk["Pubkey"].from_string(wallet_address)

        class _SameWalletAdapter(sdk["Wallet"]):
            def __init__(self, payer, public_key):
                super().__init__(payer)
                self._public_key = public_key

            @property
            def public_key(self):
                return self._public_key

            def sign_transaction(self, tx):
                raise DriftTxBuilderWalletError(
                    "Same-wallet Drift prepare only builds unsigned transactions."
                )

            def sign_all_transactions(self, txs):
                raise DriftTxBuilderWalletError(
                    "Same-wallet Drift prepare only builds unsigned transactions."
                )

        connection = sdk["AsyncClient"](settings.DRIFT_RPC_URL)
        wallet = _SameWalletAdapter(sdk["Keypair"](), wallet_pubkey)
        drift_client = sdk["DriftClient"](
            connection,
            wallet,
            "mainnet",
            authority=wallet_pubkey,
            active_sub_account_id=sub_account_id,
            sub_account_ids=[sub_account_id],
        )

        try:
            if hasattr(drift_client, "subscribe"):
                await drift_client.subscribe()

            ix = ix_builder(drift_client)
            blockhash_response = await connection.get_latest_blockhash()
            blockhash_value = blockhash_response.value
            blockhash = blockhash_value.blockhash
            last_valid_block_height = getattr(blockhash_value, "last_valid_block_height", None)

            message = sdk["MessageV0"].try_compile(
                wallet_pubkey,
                [ix],
                [],
                blockhash,
            )
            unsigned_message_bytes = bytes(sdk["to_bytes_versioned"](message))
            unsigned_transaction = sdk["VersionedTransaction"](
                message,
                [sdk["NullSigner"](wallet_pubkey)],
            )
            unsigned_transaction_bytes = bytes(unsigned_transaction)

            user_account_public_key = str(
                drift_client.get_user_account_public_key(sub_account_id)
            )
            user_stats_public_key = str(drift_client.get_user_stats_public_key())
            state_public_key = str(drift_client.get_state_public_key())

            return {
                "classification": classification,
                "action": action,
                "market_type": market_type,
                "sub_account_id": sub_account_id,
                "wallet_address": wallet_address,
                "authority": wallet_address,
                "user_account_public_key": user_account_public_key,
                "user_stats_public_key": user_stats_public_key,
                "state_public_key": state_public_key,
                "recent_blockhash": str(blockhash),
                "last_valid_block_height": last_valid_block_height,
                "message_version": "v0",
                "transaction_encoding": "base64",
                "unsigned_transaction": base64.b64encode(unsigned_transaction_bytes).decode("utf-8"),
                "unsigned_message": base64.b64encode(unsigned_message_bytes).decode("utf-8"),
                "signing_instructions": [
                    "Deserialize the unsigned_transaction bytes as a versioned Solana transaction.",
                    "Replace the null signer for the authenticated wallet with a real wallet signature.",
                    "Submit the fully signed transaction bytes to POST /api/drift/execution/submit.",
                ],
            }
        finally:
            if hasattr(drift_client, "unsubscribe"):
                with suppress(Exception):
                    await drift_client.unsubscribe()
            with suppress(Exception):
                await connection.close()

    async def build_place_perp_order_payload(
        self,
        *,
        wallet_address: str,
        sub_account_id: int,
        order_intent: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build an unsigned same-wallet Drift perp-order transaction payload."""
        sdk = self._load_sdk()
        order_params = self._build_order_params(order_intent, sdk)
        return await self._build_single_ix_payload(
            wallet_address=wallet_address,
            sub_account_id=sub_account_id,
            ix_builder=lambda drift_client: drift_client.get_place_perp_order_ix(
                order_params, sub_account_id=sub_account_id
            ),
            classification="same_wallet_mobile_signing_payload",
            action="place_perp_order",
            market_type="perp",
        )

    async def build_cancel_order_payload(
        self,
        *,
        wallet_address: str,
        sub_account_id: int,
        order_id: Optional[str] = None,
        user_order_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Build an unsigned same-wallet Drift cancel-order transaction payload."""
        parsed_order_id = None
        if order_id is not None:
            parsed_order_id = self._parse_required_int(order_id, "order_id")
        if parsed_order_id is None and user_order_id is None:
            raise DriftTxBuilderValidationError(
                "Provide order_id or user_order_id to build a Drift cancel-order payload."
            )
        if user_order_id is not None:
            parsed_user_order_id = self._parse_required_int(user_order_id, "user_order_id")
            return await self._build_single_ix_payload(
                wallet_address=wallet_address,
                sub_account_id=sub_account_id,
                ix_builder=lambda drift_client: drift_client.get_cancel_order_by_user_id_ix(
                    parsed_user_order_id, sub_account_id=sub_account_id
                ),
                classification="same_wallet_mobile_signing_payload",
                action="cancel_order",
                market_type="perp",
            )

        return await self._build_single_ix_payload(
            wallet_address=wallet_address,
            sub_account_id=sub_account_id,
            ix_builder=lambda drift_client: drift_client.get_cancel_order_ix(
                order_id=parsed_order_id, sub_account_id=sub_account_id
            ),
            classification="same_wallet_mobile_signing_payload",
            action="cancel_order",
            market_type="perp",
        )


_drift_execution_tx_builder: Optional[DriftExecutionTxBuilder] = None


def get_drift_execution_tx_builder() -> DriftExecutionTxBuilder:
    """Return singleton Drift execution transaction builder."""
    global _drift_execution_tx_builder
    if _drift_execution_tx_builder is None:
        _drift_execution_tx_builder = DriftExecutionTxBuilder()
    return _drift_execution_tx_builder


__all__ = [
    "DriftTxBuilderWalletError",
    "DriftTxBuilderValidationError",
    "DriftExecutionTxBuilder",
    "get_drift_execution_tx_builder",
]
