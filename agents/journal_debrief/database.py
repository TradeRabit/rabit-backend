"""Persistent JSON storage for structured trade debrief entries."""
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


class TradeDebriefDatabase:
    """Lightweight JSON-backed store for structured trade debrief entries."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.TRADE_DEBRIEF_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self.data: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Load trade debrief entries from disk."""
        with self._lock:
            if not self.db_path.exists():
                self.data = {}
                logger.info("Trade debrief database file not found, starting fresh")
                return

            try:
                with open(self.db_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                self.data = payload if isinstance(payload, dict) else {}
                logger.info(f"Loaded {len(self.data)} trade debrief entries from database")
            except Exception as exc:
                logger.error(f"Error loading trade debrief database: {exc}")
                self.data = {}

    def save(self) -> None:
        """Persist trade debrief entries to disk."""
        with self._lock:
            with open(self.db_path, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, ensure_ascii=False, default=str)

    def upsert_entry(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Create or replace one trade debrief entry."""
        with self._lock:
            self.data[record["id"]] = record
            self.save()
        return dict(record)

    def list_entries(
        self,
        *,
        user_id: str,
        symbol: Optional[str] = None,
        exchange: Optional[str] = None,
        limit: Optional[int] = 20,
    ) -> List[Dict[str, Any]]:
        """List one user's trade debrief entries with optional filters."""
        normalized_symbol = str(symbol or "").strip().upper()
        normalized_exchange = str(exchange or "").strip().lower()
        records = []
        with self._lock:
            for record in self.data.values():
                if record.get("user_id") != user_id:
                    continue
                if normalized_symbol and str(record.get("symbol") or "").upper() != normalized_symbol:
                    continue
                if normalized_exchange and str(record.get("exchange") or "").strip().lower() != normalized_exchange:
                    continue
                records.append(dict(record))
        records.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        if limit is not None:
            records = records[: max(0, int(limit))]
        return records


_trade_debrief_database: Optional[TradeDebriefDatabase] = None


def get_trade_debrief_database(
    db_path: Optional[str] = None,
) -> TradeDebriefDatabase:
    """Return singleton trade debrief database."""
    global _trade_debrief_database
    if _trade_debrief_database is None:
        _trade_debrief_database = TradeDebriefDatabase(db_path)
    return _trade_debrief_database
