"""Service layer for editable user profile usernames."""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from .database import get_user_profile_database, utc_now_iso


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,31}$")


class UsernameValidationError(ValueError):
    """Raised when a username does not meet validation requirements."""


class UserProfileService:
    """Manage per-user profile records."""

    def __init__(self, db=None):
        self.db = db or get_user_profile_database()

    @staticmethod
    def _normalize_username(username: str) -> str:
        return str(username or "").strip()

    def validate_username(self, username: str) -> str:
        """Validate and normalize a proposed username."""
        normalized = self._normalize_username(username)
        if not normalized:
            raise UsernameValidationError("username is required.")
        if len(normalized) < 3 or len(normalized) > 32:
            raise UsernameValidationError("username must be between 3 and 32 characters.")
        if not USERNAME_PATTERN.fullmatch(normalized):
            raise UsernameValidationError(
                "username may only contain letters, numbers, dots, underscores, and dashes, and must start with a letter or number."
            )
        return normalized

    def get_profile(self, *, user_id: str, wallet_address: Optional[str] = None) -> Dict[str, Any]:
        """Return one profile, optionally creating a shell record on demand."""
        normalized_user_id = str(user_id or "").strip()
        if not normalized_user_id:
            raise ValueError("user_id is required.")

        record = self.db.get_profile(normalized_user_id)
        if record is None:
            return {
                "user_id": normalized_user_id,
                "wallet_address": wallet_address,
                "username": None,
                "created_at": None,
                "updated_at": None,
            }

        if wallet_address and record.get("wallet_address") != wallet_address:
            record["wallet_address"] = wallet_address
            record["updated_at"] = utc_now_iso()
            self.db.upsert_profile(record)

        return self._public_record(record)

    def set_username(self, *, user_id: str, wallet_address: Optional[str], username: str) -> Dict[str, Any]:
        """Create or update a username for one user."""
        normalized_user_id = str(user_id or "").strip()
        if not normalized_user_id:
            raise ValueError("user_id is required.")

        validated_username = self.validate_username(username)
        now = utc_now_iso()
        record = self.db.get_profile(normalized_user_id) or {
            "user_id": normalized_user_id,
            "wallet_address": wallet_address,
            "username": None,
            "created_at": now,
            "updated_at": now,
        }

        if wallet_address:
            record["wallet_address"] = wallet_address
        if not record.get("created_at"):
            record["created_at"] = now
        record["username"] = validated_username
        record["updated_at"] = now
        self.db.upsert_profile(record)
        return self._public_record(record)

    @staticmethod
    def _public_record(record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "user_id": record.get("user_id"),
            "wallet_address": record.get("wallet_address"),
            "username": record.get("username"),
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
        }


_user_profile_service: Optional[UserProfileService] = None


def get_user_profile_service(db_path: Optional[str] = None) -> UserProfileService:
    """Return the singleton user profile service."""
    global _user_profile_service
    if db_path is not None:
        return UserProfileService(get_user_profile_database(db_path))
    if _user_profile_service is None:
        _user_profile_service = UserProfileService()
    return _user_profile_service
