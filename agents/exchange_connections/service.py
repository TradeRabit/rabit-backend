"""Service layer for per-user exchange credential storage and retrieval."""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .crypto import decrypt_secret, encrypt_secret
from .database import get_exchange_connections_database, utc_now_iso


class ExchangeConnectionNotFoundError(ValueError):
    """Raised when a requested exchange connection is missing."""


class ExchangeConnectionOwnershipError(ValueError):
    """Raised when a user attempts to access another user's connection."""


class ExchangeConnectionService:
    """Manage encrypted exchange connections for users."""

    def __init__(self, db=None):
        self.db = db or get_exchange_connections_database()

    def create_connection(
        self,
        *,
        user_id: str,
        exchange: str,
        api_key: str,
        api_secret: str,
        label: Optional[str] = None,
        trading_enabled: bool = False,
        read_only: bool = True,
        is_active: bool = True,
    ) -> Dict[str, Any]:
        """Create and persist a new exchange connection."""
        normalized_exchange = (exchange or "").strip().lower()
        if not user_id:
            raise ValueError("user_id is required for exchange connections.")
        if not normalized_exchange:
            raise ValueError("exchange is required for exchange connections.")
        if not api_key.strip():
            raise ValueError("api_key is required.")
        if not api_secret.strip():
            raise ValueError("api_secret is required.")

        connection_id = str(uuid4())
        now = utc_now_iso()
        record = {
            "id": connection_id,
            "user_id": user_id,
            "exchange": normalized_exchange,
            "label": (label or f"{normalized_exchange.title()} connection").strip(),
            "api_key_ciphertext": encrypt_secret(api_key.strip()),
            "api_secret_ciphertext": encrypt_secret(api_secret.strip()),
            "last4": api_key.strip()[-4:],
            "fingerprint": hashlib.sha256(api_key.strip().encode("utf-8")).hexdigest()[:16],
            "trading_enabled": bool(trading_enabled),
            "read_only": bool(read_only),
            "is_active": bool(is_active),
            "created_at": now,
            "updated_at": now,
            "last_used_at": None,
            "revoked_at": None,
        }
        self.db.upsert_connection(record)
        if record["is_active"]:
            self.db.deactivate_other_connections(
                user_id=user_id,
                exchange=normalized_exchange,
                keep_connection_id=connection_id,
            )
        return self._public_record(record)

    def list_connections(self, *, user_id: str, exchange: Optional[str] = None) -> List[Dict[str, Any]]:
        """List one user's stored exchange connections."""
        records = self.db.list_connections(user_id=user_id)
        if exchange:
            normalized_exchange = exchange.strip().lower()
            records = [
                record
                for record in records
                if record.get("exchange") == normalized_exchange
            ]
        return [self._public_record(record) for record in records]

    def update_connection(
        self,
        *,
        user_id: str,
        connection_id: str,
        label: Optional[str] = None,
        trading_enabled: Optional[bool] = None,
        read_only: Optional[bool] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update mutable connection metadata."""
        record = self._get_owned_record(user_id=user_id, connection_id=connection_id)
        if label is not None:
            record["label"] = label.strip() or record["label"]
        if trading_enabled is not None:
            record["trading_enabled"] = bool(trading_enabled)
        if read_only is not None:
            record["read_only"] = bool(read_only)
        if is_active is not None:
            record["is_active"] = bool(is_active)
        record["updated_at"] = utc_now_iso()
        self.db.upsert_connection(record)
        if record["is_active"]:
            self.db.deactivate_other_connections(
                user_id=user_id,
                exchange=record["exchange"],
                keep_connection_id=connection_id,
            )
        return self._public_record(record)

    def delete_connection(self, *, user_id: str, connection_id: str) -> Dict[str, Any]:
        """Delete one owned connection."""
        record = self._get_owned_record(user_id=user_id, connection_id=connection_id)
        deleted = self.db.delete_connection(connection_id)
        return {
            "success": deleted,
            "connection_id": connection_id,
            "user_id": user_id,
            "exchange": record["exchange"],
        }

    def get_active_credentials(
        self,
        *,
        user_id: str,
        exchange: str,
        require_trading_enabled: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Return decrypted credentials for the active connection, if any."""
        normalized_exchange = exchange.strip().lower()
        for record in self.db.list_connections(user_id=user_id):
            if record.get("exchange") != normalized_exchange:
                continue
            if not record.get("is_active", False):
                continue
            if require_trading_enabled and (
                not record.get("trading_enabled", False) or record.get("read_only", True)
            ):
                raise ValueError(
                    f"Active {normalized_exchange} connection is read-only or trading is disabled."
                )

            record["last_used_at"] = utc_now_iso()
            record["updated_at"] = utc_now_iso()
            self.db.upsert_connection(record)
            return {
                "connection_id": record["id"],
                "exchange": record["exchange"],
                "label": record["label"],
                "api_key": decrypt_secret(record["api_key_ciphertext"]),
                "api_secret": decrypt_secret(record["api_secret_ciphertext"]),
                "trading_enabled": bool(record.get("trading_enabled", False)),
                "read_only": bool(record.get("read_only", True)),
            }
        return None

    def _get_owned_record(self, *, user_id: str, connection_id: str) -> Dict[str, Any]:
        """Return one record and enforce ownership."""
        record = self.db.get_connection(connection_id)
        if record is None:
            raise ExchangeConnectionNotFoundError(
                f"Exchange connection '{connection_id}' was not found."
            )
        if record.get("user_id") != user_id:
            raise ExchangeConnectionOwnershipError(
                f"Exchange connection '{connection_id}' does not belong to user '{user_id}'."
            )
        return record

    @staticmethod
    def _public_record(record: Dict[str, Any]) -> Dict[str, Any]:
        """Return safe metadata without encrypted secrets."""
        return {
            "id": record["id"],
            "user_id": record["user_id"],
            "exchange": record["exchange"],
            "label": record["label"],
            "last4": record.get("last4", ""),
            "fingerprint": record.get("fingerprint", ""),
            "trading_enabled": bool(record.get("trading_enabled", False)),
            "read_only": bool(record.get("read_only", True)),
            "is_active": bool(record.get("is_active", False)),
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
            "last_used_at": record.get("last_used_at"),
            "revoked_at": record.get("revoked_at"),
        }


_exchange_connection_service: Optional[ExchangeConnectionService] = None


def get_exchange_connection_service() -> ExchangeConnectionService:
    """Return singleton exchange connection service."""
    global _exchange_connection_service
    if _exchange_connection_service is None:
        _exchange_connection_service = ExchangeConnectionService()
    return _exchange_connection_service
