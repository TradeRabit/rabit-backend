"""Persistent nonce store for wallet-based mobile authentication."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class WalletNonceStore:
    """JSON-backed nonce store with TTL and single-use semantics."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.WALLET_AUTH_NONCE_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self.data: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Load nonce records from disk."""
        with self._lock:
            if not self.db_path.exists():
                self.data = {}
                return
            try:
                with open(self.db_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                self.data = payload if isinstance(payload, dict) else {}
            except Exception as exc:
                logger.error(f"Error loading wallet nonce store: {exc}")
                self.data = {}

    def save(self) -> None:
        """Persist nonce records to disk."""
        with self._lock:
            with open(self.db_path, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, ensure_ascii=False, default=str)

    def cleanup(self) -> None:
        """Remove expired and already-used nonce records."""
        now = utc_now()
        with self._lock:
            keys_to_delete = []
            for nonce, record in self.data.items():
                expires_at = datetime.fromisoformat(record["expires_at"])
                if expires_at <= now:
                    keys_to_delete.append(nonce)
                    continue
                if record.get("used_at"):
                    keys_to_delete.append(nonce)
            if keys_to_delete:
                for nonce in keys_to_delete:
                    self.data.pop(nonce, None)
                self.save()

    def create_nonce(self, *, wallet_address: str, message: str, nonce: str) -> Dict[str, Any]:
        """Create one nonce challenge record."""
        self.cleanup()
        now = utc_now()
        record = {
            "nonce": nonce,
            "wallet_address": wallet_address,
            "message": message,
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(seconds=settings.WALLET_AUTH_NONCE_TTL_SECONDS)).isoformat(),
            "used_at": None,
        }
        with self._lock:
            self.data[nonce] = record
            self.save()
        return dict(record)

    def get_nonce(self, nonce: str) -> Optional[Dict[str, Any]]:
        """Return one nonce record if it exists and has not expired."""
        self.cleanup()
        with self._lock:
            record = self.data.get(nonce)
            return dict(record) if record else None

    def mark_used(self, nonce: str) -> None:
        """Mark a nonce as consumed."""
        with self._lock:
            if nonce not in self.data:
                return
            self.data[nonce]["used_at"] = utc_now().isoformat()
            self.save()


_wallet_nonce_store: Optional[WalletNonceStore] = None


def get_wallet_nonce_store(db_path: Optional[str] = None) -> WalletNonceStore:
    """Return singleton wallet nonce store."""
    global _wallet_nonce_store
    if _wallet_nonce_store is None:
        _wallet_nonce_store = WalletNonceStore(db_path)
    return _wallet_nonce_store
