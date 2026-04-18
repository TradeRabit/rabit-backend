"""Drift auth-wallet and execution-wallet helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional


DEFAULT_DRIFT_EXECUTION_WALLET: Dict[str, Any] = {
    "mode": "same_wallet",
    "auth_wallet_address": None,
    "execution_wallet_address": None,
    "verified": False,
    "same_wallet_required": True,
    "linked_wallet_supported": False,
    "backend_held_signer_enabled": False,
    "notes": [
        "Drift v1 uses the authenticated wallet as the execution wallet.",
        "Different execution wallets are not supported yet in the backend.",
        "Backend-held signer storage is not enabled.",
    ],
}


def wallet_address_from_user_id(user_id: Optional[str]) -> Optional[str]:
    """Extract a Solana wallet address from a wallet-derived user ID."""
    if not user_id:
        return None
    prefix = "wallet:"
    if not str(user_id).startswith(prefix):
        return None
    wallet_address = str(user_id)[len(prefix) :].strip()
    return wallet_address or None


def build_drift_execution_wallet_status(user_id: Optional[str]) -> Dict[str, Any]:
    """Return the current Drift execution-wallet status for one authenticated user."""
    payload = dict(DEFAULT_DRIFT_EXECUTION_WALLET)
    payload["notes"] = list(DEFAULT_DRIFT_EXECUTION_WALLET["notes"])

    wallet_address = wallet_address_from_user_id(user_id)
    if wallet_address:
        payload["auth_wallet_address"] = wallet_address
        payload["execution_wallet_address"] = wallet_address
        payload["verified"] = True
        payload["notes"] = [
            "Drift v1 uses the authenticated wallet as the execution wallet.",
            "This user is verified through wallet-auth JWT identity.",
            "Different execution wallets must wait for a later linking flow.",
        ]
    else:
        payload["notes"] = [
            "No authenticated wallet user is active for this request.",
            "Drift execution wallet status can only be verified from wallet-auth identity.",
            "Different execution wallets are not supported yet in the backend.",
        ]

    return payload


__all__ = [
    "DEFAULT_DRIFT_EXECUTION_WALLET",
    "wallet_address_from_user_id",
    "build_drift_execution_wallet_status",
]
