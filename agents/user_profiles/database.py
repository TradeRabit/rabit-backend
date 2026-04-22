"""JSON persistence for editable user profiles."""
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
    """Return a timezone-aware UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


class UserProfileDatabase:
    """Lightweight JSON-backed store for user profile records."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.USER_PROFILES_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self.data: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Load profile records from disk."""
        with self._lock:
            if not self.db_path.exists():
                self.data = {}
                logger.info("User profiles database file not found, starting fresh")
                return

            try:
                with open(self.db_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                self.data = payload if isinstance(payload, dict) else {}
                logger.info("Loaded %s user profiles from database", len(self.data))
            except Exception as exc:
                logger.error("Error loading user profiles database: %s", exc)
                self.data = {}

    def save(self) -> None:
        """Persist profile records to disk."""
        with self._lock:
            with open(self.db_path, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, ensure_ascii=False, default=str)

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Return one stored profile by user ID."""
        with self._lock:
            record = self.data.get(user_id)
            return dict(record) if record else None

    def upsert_profile(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Create or replace one profile record."""
        user_id = str(record.get("user_id") or "").strip()
        if not user_id:
            raise ValueError("user_id is required for user profiles.")

        with self._lock:
            self.data[user_id] = dict(record)
            self.save()
            return dict(self.data[user_id])

    def list_profiles(self) -> List[Dict[str, Any]]:
        """Return all profile records."""
        with self._lock:
            records = [dict(record) for record in self.data.values()]
        records.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return records


_user_profile_database: Optional[UserProfileDatabase] = None


def get_user_profile_database(db_path: Optional[str] = None) -> UserProfileDatabase:
    """Return the singleton user profile database."""
    global _user_profile_database
    if db_path is not None:
        return UserProfileDatabase(db_path)
    if _user_profile_database is None:
        _user_profile_database = UserProfileDatabase()
    return _user_profile_database
