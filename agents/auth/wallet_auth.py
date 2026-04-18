"""Solana wallet auth flow for mobile: nonce, signature verify, JWT issue."""
from __future__ import annotations

import base64
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from nacl.signing import VerifyKey

from .base58 import b58decode
from .jwt_auth import issue_access_token
from .nonce_store import get_wallet_nonce_store
from config.settings import settings


class WalletAuthError(ValueError):
    """Raised when wallet auth verification fails."""


def build_wallet_sign_message(*, wallet_address: str, nonce: str, issued_at: str) -> str:
    """Build the exact message the mobile wallet should sign."""
    return (
        "Rabit mobile sign-in request\n"
        f"Address: {wallet_address}\n"
        f"Nonce: {nonce}\n"
        f"Issued At: {issued_at}\n"
        f"Audience: {settings.AUTH_JWT_AUDIENCE}\n"
        f"Issuer: {settings.AUTH_JWT_ISSUER}"
    )


def create_wallet_auth_nonce(*, wallet_address: str) -> Dict[str, Any]:
    """Create a sign-in nonce and challenge message for one wallet address."""
    if not wallet_address:
        raise WalletAuthError("wallet_address is required.")

    nonce = secrets.token_urlsafe(24)
    issued_at = datetime.now(timezone.utc).isoformat()
    message = build_wallet_sign_message(
        wallet_address=wallet_address,
        nonce=nonce,
        issued_at=issued_at,
    )
    record = get_wallet_nonce_store().create_nonce(
        wallet_address=wallet_address,
        message=message,
        nonce=nonce,
    )
    return {
        "wallet_address": wallet_address,
        "nonce": record["nonce"],
        "message": record["message"],
        "issued_at": issued_at,
        "expires_at": record["expires_at"],
    }


def _decode_signature(signature: str, encoding: str) -> bytes:
    """Decode a wallet signature from supported encodings."""
    normalized = (encoding or "base64").strip().lower()
    if normalized == "base64":
        padded = signature + "=" * ((4 - len(signature) % 4) % 4)
        return base64.b64decode(padded)
    if normalized == "base58":
        return b58decode(signature)
    raise WalletAuthError("signature_encoding must be 'base64' or 'base58'.")


def verify_wallet_auth(
    *,
    wallet_address: str,
    nonce: str,
    signature: str,
    signature_encoding: str = "base64",
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify a signed wallet challenge and issue a JWT."""
    if not wallet_address:
        raise WalletAuthError("wallet_address is required.")
    if not nonce:
        raise WalletAuthError("nonce is required.")
    if not signature:
        raise WalletAuthError("signature is required.")

    record = get_wallet_nonce_store().get_nonce(nonce)
    if not record:
        raise WalletAuthError("Nonce not found or already expired.")
    if record.get("wallet_address") != wallet_address:
        raise WalletAuthError("Nonce does not belong to this wallet address.")
    if record.get("used_at"):
        raise WalletAuthError("Nonce has already been used.")

    expected_message = record["message"]
    if message is not None and message != expected_message:
        raise WalletAuthError("Signed message does not match stored challenge.")

    signature_bytes = _decode_signature(signature, signature_encoding)
    public_key = b58decode(wallet_address)
    try:
        VerifyKey(public_key).verify(expected_message.encode("utf-8"), signature_bytes)
    except Exception as exc:  # pragma: no cover - library-specific failure path
        raise WalletAuthError("Wallet signature verification failed.") from exc

    get_wallet_nonce_store().mark_used(nonce)
    token = issue_access_token(wallet_address=wallet_address)
    return {
        **token,
        "message": expected_message,
        "nonce": nonce,
    }
