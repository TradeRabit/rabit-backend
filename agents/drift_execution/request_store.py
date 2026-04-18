"""JSON-backed store for Drift execution prepare/submit records."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional
from uuid import uuid4

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Return timezone-aware UTC timestamp string."""
    return utc_now().isoformat()


class DriftExecutionRequestNotFoundError(ValueError):
    """Raised when one Drift execution request does not exist."""


class DriftExecutionRequestOwnershipError(ValueError):
    """Raised when a Drift execution request does not belong to the active user."""


class DriftExecutionRequestsDatabase:
    """Lightweight JSON persistence for Drift execution request records."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.DRIFT_EXECUTION_REQUESTS_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self.data: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Load execution request records from disk."""
        with self._lock:
            if not self.db_path.exists():
                self.data = {}
                logger.info("Drift execution request database file not found, starting fresh")
                return
            try:
                with open(self.db_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                self.data = payload if isinstance(payload, dict) else {}
                logger.info(f"Loaded {len(self.data)} Drift execution requests from database")
            except Exception as exc:
                logger.error(f"Error loading Drift execution request database: {exc}")
                self.data = {}

    def save(self) -> None:
        """Persist execution request records to disk."""
        with self._lock:
            with open(self.db_path, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, ensure_ascii=False, default=str)

    def upsert(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Create or replace one execution request record."""
        execution_id = record["execution_id"]
        with self._lock:
            self.data[execution_id] = record
            self.save()
        return dict(record)

    def get(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Fetch one execution request by ID."""
        with self._lock:
            record = self.data.get(execution_id)
            return dict(record) if record else None


class DriftExecutionRequestService:
    """Service wrapper for Drift execution prepare/submit request records."""

    def __init__(self, db: Optional[DriftExecutionRequestsDatabase] = None):
        self.db = db or get_drift_execution_requests_database()

    def create_prepared_request(
        self,
        *,
        user_id: str,
        auth_wallet_address: str,
        execution_wallet_status: Dict[str, Any],
        sub_account_id: int,
        order_intent: Dict[str, Any],
        prepared_transaction: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a prepared same-wallet Drift execution request."""
        execution_id = uuid4().hex
        prepared_at = utc_now()
        expires_at = prepared_at + timedelta(seconds=settings.DRIFT_EXECUTION_PREPARE_TTL_SECONDS)
        execution_wallet_address = execution_wallet_status.get("execution_wallet_address")

        record = {
            "execution_id": execution_id,
            "status": "prepared",
            "mode": "client_wallet_signing",
            "user_id": user_id,
            "auth_wallet_address": auth_wallet_address,
            "execution_wallet_address": execution_wallet_address,
            "same_wallet_required": True,
            "sub_account_id": sub_account_id,
            "order_intent": order_intent,
            "requires_client_signature": True,
            "prepared_transaction": prepared_transaction or {},
            "prepared_at": prepared_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "submitted_at": None,
            "transaction_signature": None,
            "last_error": None,
        }
        return self.db.upsert(record)

    def get_request(self, *, user_id: str, execution_id: str) -> Dict[str, Any]:
        """Return one owned execution request."""
        record = self.db.get(execution_id)
        if not record:
            raise DriftExecutionRequestNotFoundError(
                f"Drift execution request '{execution_id}' was not found."
            )
        if record.get("user_id") != user_id:
            raise DriftExecutionRequestOwnershipError(
                f"Drift execution request '{execution_id}' does not belong to user '{user_id}'."
            )
        return record

    def mark_submitted(
        self,
        *,
        user_id: str,
        execution_id: str,
        transaction_signature: str,
    ) -> Dict[str, Any]:
        """Mark one execution request as submitted."""
        record = self.get_request(user_id=user_id, execution_id=execution_id)
        record["status"] = "submitted"
        record["submitted_at"] = utc_now_iso()
        record["transaction_signature"] = transaction_signature
        record["last_error"] = None
        return self.db.upsert(record)

    def mark_failed(
        self,
        *,
        user_id: str,
        execution_id: str,
        error: str,
    ) -> Dict[str, Any]:
        """Mark one execution request as submit_failed."""
        record = self.get_request(user_id=user_id, execution_id=execution_id)
        record["status"] = "submit_failed"
        record["last_error"] = error
        return self.db.upsert(record)


_drift_execution_requests_db: Optional[DriftExecutionRequestsDatabase] = None
_drift_execution_request_service: Optional[DriftExecutionRequestService] = None


def get_drift_execution_requests_database(
    db_path: Optional[str] = None,
) -> DriftExecutionRequestsDatabase:
    """Return singleton Drift execution request database."""
    global _drift_execution_requests_db
    if _drift_execution_requests_db is None:
        _drift_execution_requests_db = DriftExecutionRequestsDatabase(db_path)
    return _drift_execution_requests_db


def get_drift_execution_request_service() -> DriftExecutionRequestService:
    """Return singleton Drift execution request service."""
    global _drift_execution_request_service
    if _drift_execution_request_service is None:
        _drift_execution_request_service = DriftExecutionRequestService()
    return _drift_execution_request_service


__all__ = [
    "DriftExecutionRequestNotFoundError",
    "DriftExecutionRequestOwnershipError",
    "DriftExecutionRequestsDatabase",
    "DriftExecutionRequestService",
    "get_drift_execution_requests_database",
    "get_drift_execution_request_service",
]
