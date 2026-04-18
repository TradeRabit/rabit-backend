"""Encrypted JSON persistence for user exchange connections."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def utc_now_iso() -> str:
    """Return timezone-aware UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


class ExchangeConnectionsDatabase:
    """Lightweight encrypted JSON store for exchange connection metadata."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.EXCHANGE_CONNECTIONS_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self.data: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Load exchange connection records from disk."""
        with self._lock:
            if not self.db_path.exists():
                self.data = {}
                logger.info("Exchange connections database file not found, starting fresh")
                return

            try:
                with open(self.db_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if isinstance(payload, dict):
                    self.data = payload
                else:
                    self.data = {}
                logger.info(f"Loaded {len(self.data)} exchange connections from database")
            except Exception as exc:
                logger.error(f"Error loading exchange connections database: {exc}")
                self.data = {}

    def save(self) -> None:
        """Persist exchange connection records to disk."""
        with self._lock:
            with open(self.db_path, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, ensure_ascii=False, default=str)

    def upsert_connection(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Create or replace one exchange connection record."""
        connection_id = record["id"]
        with self._lock:
            self.data[connection_id] = record
            self.save()
        return dict(record)

    def get_connection(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Fetch one connection by ID."""
        with self._lock:
            record = self.data.get(connection_id)
            return dict(record) if record else None

    def list_connections(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all connections, optionally filtered by user."""
        with self._lock:
            records = [
                dict(record)
                for record in self.data.values()
                if user_id is None or record.get("user_id") == user_id
            ]
        records.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return records

    def delete_connection(self, connection_id: str) -> bool:
        """Delete one connection."""
        with self._lock:
            if connection_id not in self.data:
                return False
            del self.data[connection_id]
            self.save()
            return True

    def deactivate_other_connections(
        self,
        *,
        user_id: str,
        exchange: str,
        keep_connection_id: str,
    ) -> None:
        """Ensure only one active connection per user/exchange pair."""
        with self._lock:
            changed = False
            for connection_id, record in self.data.items():
                if connection_id == keep_connection_id:
                    continue
                if record.get("user_id") != user_id or record.get("exchange") != exchange:
                    continue
                if not record.get("is_active", False):
                    continue
                record["is_active"] = False
                record["updated_at"] = utc_now_iso()
                changed = True
            if changed:
                self.save()


_exchange_connections_db: Optional[ExchangeConnectionsDatabase] = None


def get_exchange_connections_database(
    db_path: Optional[str] = None,
) -> ExchangeConnectionsDatabase:
    """Return singleton exchange connections database."""
    global _exchange_connections_db
    if _exchange_connections_db is None:
        _exchange_connections_db = ExchangeConnectionsDatabase(db_path)
    return _exchange_connections_db
