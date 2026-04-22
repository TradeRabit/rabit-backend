"""Helpers for Rabit contract readiness, setup transactions, and backend-signed settlement."""
from __future__ import annotations

import base64
import json
from contextlib import suppress
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from config.settings import settings
from contract import (
    derive_associated_token_account,
    derive_delegated_signer_pda,
    derive_spending_profile_pda,
    get_rabit_contract_sdk,
    load_deployment,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class ContractExecutionError(ValueError):
    """Raised when contract execution helpers cannot complete a request."""


class AiUsageAlreadySettledError(ValueError):
    """Raised when one scope has already been settled on-chain."""


class AiUsageSettlementDatabase:
    """JSON-backed idempotency store for on-chain AI usage settlements."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.RABIT_AI_USAGE_SETTLEMENTS_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self.data: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        with self._lock:
            if not self.db_path.exists():
                self.data = {}
                return
            try:
                with open(self.db_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                self.data = payload if isinstance(payload, dict) else {}
            except Exception as exc:
                logger.error(f"Error loading AI usage settlement database: {exc}")
                self.data = {}

    def save(self) -> None:
        with self._lock:
            with open(self.db_path, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, ensure_ascii=False, default=str)

    def get(self, scope_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            record = self.data.get(scope_id)
            return dict(record) if record else None

    def upsert(self, scope_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self.data[scope_id] = dict(record)
            self.save()
            return dict(self.data[scope_id])

    def list(self, *, user_id: Optional[str] = None, wallet_address: Optional[str] = None) -> list[Dict[str, Any]]:
        with self._lock:
            records = [dict(record) for record in self.data.values()]
        if user_id:
            records = [record for record in records if record.get("user_id") == user_id]
        if wallet_address:
            records = [record for record in records if record.get("wallet_address") == wallet_address]
        records.sort(key=lambda item: str(item.get("submitted_at") or ""), reverse=True)
        return records


def _load_solana_sdk() -> Dict[str, Any]:
    try:
        from solders.keypair import Keypair
        from solders.message import MessageV0, to_bytes_versioned
        from solders.null_signer import NullSigner
        from solders.pubkey import Pubkey
        from solders.transaction import VersionedTransaction
        from solana.rpc.async_api import AsyncClient
        from solana.rpc.types import TxOpts
    except ImportError as exc:
        raise ContractExecutionError(
            "Contract execution requires optional Solana dependencies: solders and solana."
        ) from exc

    return {
        "AsyncClient": AsyncClient,
        "Keypair": Keypair,
        "MessageV0": MessageV0,
        "NullSigner": NullSigner,
        "Pubkey": Pubkey,
        "TxOpts": TxOpts,
        "VersionedTransaction": VersionedTransaction,
        "to_bytes_versioned": to_bytes_versioned,
    }


def _load_backend_signer():
    raw = str(settings.RABIT_CONTRACT_BACKEND_SIGNER or "").strip()
    if not raw:
        raise ContractExecutionError("RABIT_CONTRACT_BACKEND_SIGNER is not configured.")

    sdk = _load_solana_sdk()
    keypair_cls = sdk["Keypair"]

    with suppress(Exception):
        return keypair_cls.from_base58_string(raw)

    with suppress(Exception):
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return keypair_cls.from_bytes(bytes(int(value) for value in parsed))

    with suppress(Exception):
        return keypair_cls.from_bytes(base64.b64decode(raw))

    raise ContractExecutionError(
        "RABIT_CONTRACT_BACKEND_SIGNER must be a base58 private key string, base64 bytes, or JSON byte array."
    )


def get_backend_signer_pubkey() -> Optional[str]:
    with suppress(Exception):
        return str(_load_backend_signer().pubkey())
    return None


def ensure_backend_matches_contract_authority() -> str:
    """Return backend signer pubkey after verifying it matches deployed contract authority."""
    deployment = load_deployment(settings.RABIT_CONTRACT_CLUSTER)
    authority_wallet = str(deployment.authority_wallet or "").strip()
    if not authority_wallet:
        raise ContractExecutionError("Contract deployment metadata has no authority wallet configured.")
    signer_pubkey = get_backend_signer_pubkey()
    if not signer_pubkey:
        raise ContractExecutionError("Backend contract signer is not configured or could not be loaded.")
    if signer_pubkey != authority_wallet:
        raise ContractExecutionError(
            "Configured backend contract signer does not match the deployed contract authority wallet."
        )
    return signer_pubkey


async def _get_latest_blockhash(rpc_url: str) -> tuple[Any, Optional[int]]:
    sdk = _load_solana_sdk()
    client = sdk["AsyncClient"](rpc_url)
    try:
        response = await client.get_latest_blockhash()
    finally:
        await client.close()

    value = response.value
    return value.blockhash, getattr(value, "last_valid_block_height", None)


async def build_unsigned_instruction_payload(
    *,
    payer: str,
    instruction: Any,
    classification: str,
    action: str,
    rpc_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Wrap one instruction in an unsigned versioned transaction payload for mobile signing."""
    sdk = _load_solana_sdk()
    deployment = load_deployment(settings.RABIT_CONTRACT_CLUSTER)
    resolved_rpc_url = rpc_url or settings.RABIT_CONTRACT_RPC_URL or settings.DRIFT_RPC_URL
    blockhash, last_valid_block_height = await _get_latest_blockhash(resolved_rpc_url)
    payer_pubkey = sdk["Pubkey"].from_string(payer)

    message = sdk["MessageV0"].try_compile(
        payer_pubkey,
        [instruction],
        [],
        blockhash,
    )
    unsigned_message_bytes = bytes(sdk["to_bytes_versioned"](message))
    unsigned_transaction = sdk["VersionedTransaction"](
        message,
        [sdk["NullSigner"](payer_pubkey)],
    )
    unsigned_transaction_bytes = bytes(unsigned_transaction)

    return {
        "classification": classification,
        "action": action,
        "cluster": deployment.cluster,
        "program_id": deployment.program_id,
        "authority": payer,
        "recent_blockhash": str(blockhash),
        "last_valid_block_height": last_valid_block_height,
        "message_version": "v0",
        "transaction_encoding": "base64",
        "unsigned_transaction": base64.b64encode(unsigned_transaction_bytes).decode("utf-8"),
        "unsigned_message": base64.b64encode(unsigned_message_bytes).decode("utf-8"),
        "signing_instructions": [
            "Deserialize the unsigned_transaction bytes as a versioned Solana transaction.",
            "Replace the null signer for the authenticated wallet with a real wallet signature.",
            "Submit the fully signed transaction bytes to POST /api/contract/setup/submit.",
        ],
    }


async def submit_signed_transaction(
    *,
    signed_transaction: bytes,
    rpc_url: Optional[str] = None,
    skip_preflight: bool = False,
    max_retries: Optional[int] = None,
) -> str:
    """Submit a pre-signed raw transaction to Solana RPC."""
    sdk = _load_solana_sdk()
    resolved_rpc_url = rpc_url or settings.RABIT_CONTRACT_RPC_URL or settings.DRIFT_RPC_URL
    client = sdk["AsyncClient"](resolved_rpc_url)
    try:
        response = await client.send_raw_transaction(
            signed_transaction,
            opts=sdk["TxOpts"](
                skip_preflight=skip_preflight,
                max_retries=max_retries,
            ),
        )
    finally:
        await client.close()

    return str(response.value)


async def submit_backend_signed_instruction(
    *,
    instruction: Any,
    payer: Optional[str] = None,
    rpc_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Sign and submit one contract instruction with the configured backend authority keypair."""
    sdk = _load_solana_sdk()
    backend_signer = _load_backend_signer()
    resolved_rpc_url = rpc_url or settings.RABIT_CONTRACT_RPC_URL or settings.DRIFT_RPC_URL
    payer_pubkey = sdk["Pubkey"].from_string(payer) if payer else backend_signer.pubkey()

    client = sdk["AsyncClient"](resolved_rpc_url)
    try:
        blockhash_response = await client.get_latest_blockhash()
        blockhash_value = blockhash_response.value
        blockhash = blockhash_value.blockhash
        last_valid_block_height = getattr(blockhash_value, "last_valid_block_height", None)

        message = sdk["MessageV0"].try_compile(
            payer_pubkey,
            [instruction],
            [],
            blockhash,
        )
        transaction = sdk["VersionedTransaction"](message, [backend_signer])
        raw_tx = bytes(transaction)
        response = await client.send_raw_transaction(raw_tx)
    finally:
        await client.close()

    return {
        "transaction_signature": str(response.value),
        "recent_blockhash": str(blockhash),
        "last_valid_block_height": last_valid_block_height,
        "transaction_encoding": "base64",
        "signed_transaction": base64.b64encode(raw_tx).decode("utf-8"),
        "signer": str(backend_signer.pubkey()),
        "rpc_url": resolved_rpc_url,
    }


async def fetch_token_account_balance(*, token_account: str, rpc_url: Optional[str] = None) -> Dict[str, Any]:
    """Return token account balance details, or a missing-account payload when absent."""
    sdk = _load_solana_sdk()
    resolved_rpc_url = rpc_url or settings.RABIT_CONTRACT_RPC_URL or settings.DRIFT_RPC_URL
    client = sdk["AsyncClient"](resolved_rpc_url)
    try:
        account_info = await client.get_account_info(sdk["Pubkey"].from_string(token_account))
        exists = getattr(account_info, "value", None) is not None
        if not exists:
            return {
                "exists": False,
                "amount": 0,
                "decimals": settings.RABIT_AI_USAGE_PAYMENT_MINT_DECIMALS,
                "ui_amount": 0.0,
                "ui_amount_string": "0",
            }
        balance_response = await client.get_token_account_balance(sdk["Pubkey"].from_string(token_account))
    finally:
        await client.close()

    value = balance_response.value
    return {
        "exists": True,
        "amount": int(getattr(value, "amount", 0) or 0),
        "decimals": int(getattr(value, "decimals", settings.RABIT_AI_USAGE_PAYMENT_MINT_DECIMALS) or 0),
        "ui_amount": float(getattr(value, "ui_amount", 0.0) or 0.0),
        "ui_amount_string": str(getattr(value, "ui_amount_string", "0")),
    }


async def get_contract_readiness(*, wallet_address: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Return setup and balance readiness for one authenticated wallet user."""
    payment_mint = settings.RABIT_AI_USAGE_PAYMENT_MINT
    if not payment_mint:
        raise ContractExecutionError("RABIT_AI_USAGE_PAYMENT_MINT is not configured.")

    deployment = load_deployment(settings.RABIT_CONTRACT_CLUSTER)
    sdk = get_rabit_contract_sdk()
    spending_profile = await sdk.get_spending_profile(wallet_address)
    delegated_signer = None
    if deployment.backend_authority_wallet:
        delegated_signer = await sdk.get_delegated_signer(wallet_address, deployment.backend_authority_wallet)

    user_token_account = derive_associated_token_account(wallet_address, payment_mint)
    fee_recipient_token_account = derive_associated_token_account(deployment.fee_recipient_pda, payment_mint)
    user_balance = await fetch_token_account_balance(token_account=user_token_account, rpc_url=sdk.rpc_url)
    fee_recipient_balance = await fetch_token_account_balance(
        token_account=fee_recipient_token_account,
        rpc_url=sdk.rpc_url,
    )
    balance_usd = round(
        float(user_balance["ui_amount"] or 0.0) * settings.RABIT_AI_USAGE_PAYMENT_TOKEN_USD_PRICE,
        10,
    )
    minimum_balance_usd = settings.RABIT_AI_USAGE_CHAT_MIN_BALANCE_USD
    balance_ok = balance_usd >= minimum_balance_usd
    now_ts = int(datetime.now(timezone.utc).timestamp())
    delegated_signer_expired = bool(
        delegated_signer is not None
        and int(getattr(delegated_signer, "expires_at", 0) or 0) > 0
        and int(getattr(delegated_signer, "expires_at", 0) or 0) <= now_ts
    )

    notes = []
    if spending_profile is None:
        notes.append("Spending profile is not initialized.")
    elif str(spending_profile.payment_mint) != payment_mint:
        notes.append("Spending profile payment mint does not match backend payment mint configuration.")
    if delegated_signer is None:
        notes.append("Delegated signer is not initialized for the backend authority.")
    elif not delegated_signer.is_active:
        notes.append("Delegated signer exists but is not active.")
    elif delegated_signer_expired:
        notes.append("Delegated signer has expired and must be renewed.")
    if not user_balance["exists"]:
        notes.append("User payment token account does not exist yet.")
    if not fee_recipient_balance["exists"]:
        notes.append("Fee recipient token account does not exist yet.")
    if not balance_ok:
        notes.append(
            f"Payment balance is below the required minimum of ${minimum_balance_usd:.2f}."
        )

    backend_signer_ready = False
    backend_signer_pubkey = None
    with suppress(Exception):
        backend_signer = _load_backend_signer()
        backend_signer_ready = True
        backend_signer_pubkey = str(backend_signer.pubkey())

    spending_profile_pda = None
    delegated_signer_pda = None
    with suppress(Exception):
        spending_profile_pda = derive_spending_profile_pda(
            wallet_address,
            cluster=deployment.cluster,
            program_id=deployment.program_id,
        )[0]
    with suppress(Exception):
        delegated_signer_pda = derive_delegated_signer_pda(
            wallet_address,
            deployment.backend_authority_wallet,
            cluster=deployment.cluster,
            program_id=deployment.program_id,
        )[0]

    setup_complete = bool(
        spending_profile is not None
        and delegated_signer is not None
        and delegated_signer.is_active
        and not delegated_signer_expired
        and user_balance["exists"]
        and fee_recipient_balance["exists"]
    )

    return {
        "user_id": user_id,
        "wallet_address": wallet_address,
        "cluster": deployment.cluster,
        "program_id": deployment.program_id,
        "backend_authority_wallet": deployment.backend_authority_wallet,
        "backend_signer_ready": backend_signer_ready,
        "backend_signer_pubkey": backend_signer_pubkey,
        "payment_mint": payment_mint,
        "payment_token_symbol": settings.RABIT_AI_USAGE_PAYMENT_TOKEN_SYMBOL,
        "payment_mint_decimals": settings.RABIT_AI_USAGE_PAYMENT_MINT_DECIMALS,
        "payment_token_usd_price": settings.RABIT_AI_USAGE_PAYMENT_TOKEN_USD_PRICE,
        "minimum_balance_usd": minimum_balance_usd,
        "user_token_account": user_token_account,
        "fee_recipient_token_account": fee_recipient_token_account,
        "user_token_account_exists": bool(user_balance["exists"]),
        "fee_recipient_token_account_exists": bool(fee_recipient_balance["exists"]),
        "payment_balance_amount": int(user_balance["amount"]),
        "payment_balance_ui_amount": float(user_balance["ui_amount"]),
        "payment_balance_usd": balance_usd,
        "balance_ok": balance_ok,
        "spending_profile_pda": spending_profile_pda,
        "spending_profile_exists": spending_profile is not None,
        "spending_profile_usage_sequence": int(spending_profile.usage_sequence) if spending_profile else None,
        "spending_profile_payment_mint": str(spending_profile.payment_mint) if spending_profile else None,
        "delegated_signer_pda": delegated_signer_pda,
        "delegated_signer_exists": delegated_signer is not None,
        "delegated_signer_active": bool(delegated_signer.is_active) if delegated_signer else False,
        "delegated_signer_expired": delegated_signer_expired,
        "delegated_signer_expires_at": int(delegated_signer.expires_at) if delegated_signer else None,
        "delegated_signer_spending_limit": int(delegated_signer.spending_limit) if delegated_signer else None,
        "setup_complete": setup_complete,
        "can_chat": bool(settings.RABIT_AI_USAGE_ENFORCE_CHAT_BALANCE is False or (setup_complete and balance_ok)),
        "notes": notes,
    }


_ai_usage_settlement_db: Optional[AiUsageSettlementDatabase] = None


def get_ai_usage_settlement_database() -> AiUsageSettlementDatabase:
    global _ai_usage_settlement_db
    if _ai_usage_settlement_db is None:
        _ai_usage_settlement_db = AiUsageSettlementDatabase()
    return _ai_usage_settlement_db


__all__ = [
    "AiUsageAlreadySettledError",
    "AiUsageSettlementDatabase",
    "ContractExecutionError",
    "build_unsigned_instruction_payload",
    "ensure_backend_matches_contract_authority",
    "fetch_token_account_balance",
    "get_backend_signer_pubkey",
    "get_ai_usage_settlement_database",
    "get_contract_readiness",
    "submit_backend_signed_instruction",
    "submit_signed_transaction",
]
