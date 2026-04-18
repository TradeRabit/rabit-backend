"""OpenRouter session cost ledger keyed by agent scope_id."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional

from config.settings import settings
from utils.logger import get_logger

from .database import get_models_database

logger = get_logger(__name__)


def utc_now_iso() -> str:
    """Return a timezone-aware UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


def _to_int(value: Any) -> int:
    """Safely coerce optional usage values into ints."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _round_cost(value: float) -> float:
    """Round estimated USD cost to a stable precision."""
    return round(float(value or 0.0), 10)


class OpenRouterSessionCostDatabase:
    """Lightweight JSON-backed store for accumulated session costs."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.OPENROUTER_SESSION_COST_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self.data: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Load stored session costs from disk."""
        with self._lock:
            if not self.db_path.exists():
                self.data = {}
                logger.info("OpenRouter session cost database file not found, starting fresh")
                return

            try:
                with open(self.db_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                self.data = payload if isinstance(payload, dict) else {}
                logger.info(f"Loaded {len(self.data)} OpenRouter session cost records from database")
            except Exception as exc:
                logger.error(f"Error loading OpenRouter session cost database: {exc}")
                self.data = {}

    def save(self) -> None:
        """Persist session costs to disk."""
        with self._lock:
            with open(self.db_path, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, ensure_ascii=False, default=str)

    def get_scope(self, scope_id: str) -> Optional[Dict[str, Any]]:
        """Return one stored scope summary if present."""
        with self._lock:
            record = self.data.get(scope_id)
            return dict(record) if record else None

    def upsert_scope(self, scope_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Create or replace one scope summary."""
        with self._lock:
            self.data[scope_id] = dict(record)
            self.save()
            return dict(self.data[scope_id])


class OpenRouterSessionCostService:
    """Aggregate estimated OpenRouter costs for one chat/session scope."""

    def __init__(self, db: Optional[OpenRouterSessionCostDatabase] = None):
        self.db = db or get_openrouter_session_cost_database()
        self.models_db = get_models_database()

    def record_usage(
        self,
        *,
        scope_id: str,
        user_id: Optional[str],
        model_id: str,
        usage: Dict[str, Any],
        phase: str,
    ) -> Dict[str, Any]:
        """Record one OpenRouter usage event and return the updated scope summary."""
        normalized_scope_id = str(scope_id or "").strip()
        if not normalized_scope_id:
            raise ValueError("scope_id is required for session cost tracking.")

        normalized_phase = str(phase or "response").strip().lower() or "response"
        normalized_model_id = str(model_id or "").strip()
        if not normalized_model_id:
            raise ValueError("model_id is required for session cost tracking.")

        input_tokens = _to_int(usage.get("input_tokens"))
        output_tokens = _to_int(usage.get("output_tokens"))
        total_tokens = input_tokens + output_tokens

        model_info = self.models_db.get_model(normalized_model_id)
        input_price = float(model_info.input_price) if model_info else 0.0
        output_price = float(model_info.output_price) if model_info else 0.0
        input_cost_usd = (input_tokens / 1_000_000.0) * input_price
        output_cost_usd = (output_tokens / 1_000_000.0) * output_price
        estimated_cost_usd = _round_cost(input_cost_usd + output_cost_usd)
        timestamp = utc_now_iso()

        record = self.db.get_scope(normalized_scope_id) or {
            "scope_id": normalized_scope_id,
            "user_id": user_id,
            "currency": "USD",
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "model_ids": [],
            "phases": {},
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        if user_id:
            record["user_id"] = user_id

        record["total_calls"] += 1
        record["total_input_tokens"] += input_tokens
        record["total_output_tokens"] += output_tokens
        record["total_tokens"] += total_tokens
        record["estimated_cost_usd"] = _round_cost(
            float(record.get("estimated_cost_usd") or 0.0) + estimated_cost_usd
        )

        model_ids = set(record.get("model_ids", []))
        model_ids.add(normalized_model_id)
        record["model_ids"] = sorted(model_ids)

        phases = record.setdefault("phases", {})
        phase_record = phases.get(normalized_phase) or {
            "phase": normalized_phase,
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
        }
        phase_record["calls"] += 1
        phase_record["input_tokens"] += input_tokens
        phase_record["output_tokens"] += output_tokens
        phase_record["total_tokens"] += total_tokens
        phase_record["estimated_cost_usd"] = _round_cost(
            float(phase_record.get("estimated_cost_usd") or 0.0) + estimated_cost_usd
        )
        phases[normalized_phase] = phase_record

        record["updated_at"] = timestamp
        return self.db.upsert_scope(normalized_scope_id, record)

    def get_scope_summary(
        self,
        *,
        scope_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Return one accumulated scope summary with normalized phase ordering."""
        normalized_scope_id = str(scope_id or "").strip()
        if not normalized_scope_id:
            return None

        record = self.db.get_scope(normalized_scope_id)
        if not record:
            return None

        phases = record.get("phases", {})
        record["phases"] = [
            phases[key]
            for key in sorted(phases.keys())
        ]
        return record


_openrouter_session_cost_database: Optional[OpenRouterSessionCostDatabase] = None
_openrouter_session_cost_service: Optional[OpenRouterSessionCostService] = None


def get_openrouter_session_cost_database(
    db_path: Optional[str] = None,
) -> OpenRouterSessionCostDatabase:
    """Return singleton OpenRouter session cost database."""
    global _openrouter_session_cost_database
    if _openrouter_session_cost_database is None:
        _openrouter_session_cost_database = OpenRouterSessionCostDatabase(db_path)
    return _openrouter_session_cost_database


def get_openrouter_session_cost_service() -> OpenRouterSessionCostService:
    """Return singleton OpenRouter session cost service."""
    global _openrouter_session_cost_service
    if _openrouter_session_cost_service is None:
        _openrouter_session_cost_service = OpenRouterSessionCostService()
    return _openrouter_session_cost_service
