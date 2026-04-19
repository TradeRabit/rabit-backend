"""Monitoring-cost ledger keyed by agent scope_id."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Return the current timezone-aware UTC timestamp string."""
    return utc_now().isoformat()


def parse_iso_timestamp(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO timestamps from stored ledger records."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def round_usd(value: float) -> float:
    """Round USD values to a stable precision for persistence."""
    return round(float(value or 0.0), 10)


def duration_seconds(started_at: Optional[str], ended_at: Optional[str] = None) -> float:
    """Return the elapsed seconds between two stored ISO timestamps."""
    started = parse_iso_timestamp(started_at)
    if started is None:
        return 0.0
    ended = parse_iso_timestamp(ended_at) or utc_now()
    return max((ended - started).total_seconds(), 0.0)


class MonitoringCostDatabase:
    """Lightweight JSON-backed store for monitoring usage costs."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.MONITORING_COST_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self.data: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Load stored monitoring costs from disk."""
        with self._lock:
            if not self.db_path.exists():
                self.data = {}
                logger.info("Monitoring cost database file not found, starting fresh")
                return

            try:
                with open(self.db_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                self.data = payload if isinstance(payload, dict) else {}
                logger.info("Loaded %s monitoring cost records from database", len(self.data))
            except Exception as exc:
                logger.error("Error loading monitoring cost database: %s", exc)
                self.data = {}

    def save(self) -> None:
        """Persist monitoring costs to disk."""
        with self._lock:
            with open(self.db_path, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, ensure_ascii=False, default=str)

    def get_scope(self, scope_id: str) -> Optional[Dict[str, Any]]:
        """Return one stored scope record if present."""
        with self._lock:
            record = self.data.get(scope_id)
            return dict(record) if record else None

    def upsert_scope(self, scope_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Create or replace one scope summary."""
        with self._lock:
            self.data[scope_id] = dict(record)
            self.save()
            return dict(self.data[scope_id])


class MonitoringCostService:
    """Accumulate monitoring costs for one chat/session scope."""

    def __init__(self, db: Optional[MonitoringCostDatabase] = None):
        self.db = db or get_monitoring_cost_database()

    def _empty_record(self, *, scope_id: str, user_id: Optional[str], timestamp: str) -> Dict[str, Any]:
        return {
            "scope_id": scope_id,
            "user_id": user_id,
            "currency": "USD",
            "alert_setup_cost_usd": 0.0,
            "trigger_cost_usd": 0.0,
            "monitoring_cost_usd": 0.0,
            "total_cost_usd": 0.0,
            "alert_setup_count": 0,
            "trigger_count": 0,
            "active_alert_count": 0,
            "active_symbol_count": 0,
            "active_symbols": [],
            "total_symbol_hours": 0.0,
            "alerts": {},
            "symbols": {},
            "created_at": timestamp,
            "updated_at": timestamp,
        }

    def _recompute(self, record: Dict[str, Any], *, now_iso: Optional[str] = None) -> Dict[str, Any]:
        """Recompute derived counters and current monitoring cost."""
        now_iso = now_iso or utc_now_iso()
        total_active_seconds = 0.0
        active_symbols = []
        active_alert_count = 0

        alerts = record.setdefault("alerts", {})
        for alert in alerts.values():
            if alert.get("status") == "active":
                active_alert_count += 1

        symbols = record.setdefault("symbols", {})
        for symbol_name, symbol_state in symbols.items():
            active_window_started_at = symbol_state.get("active_window_started_at")
            closed_active_seconds = float(symbol_state.get("closed_active_seconds") or 0.0)
            symbol_seconds = closed_active_seconds + duration_seconds(active_window_started_at, now_iso)
            total_active_seconds += symbol_seconds
            if active_window_started_at:
                active_symbols.append(symbol_name)

        total_symbol_hours = round(total_active_seconds / 3600.0, 8)
        monitoring_cost_usd = round_usd(
            total_symbol_hours * settings.MONITORING_COST_PER_SYMBOL_HOUR_USD
        )

        record["active_alert_count"] = active_alert_count
        record["active_symbol_count"] = len(active_symbols)
        record["active_symbols"] = sorted(active_symbols)
        record["total_symbol_hours"] = total_symbol_hours
        record["monitoring_cost_usd"] = monitoring_cost_usd
        record["total_cost_usd"] = round_usd(
            float(record.get("alert_setup_cost_usd") or 0.0)
            + float(record.get("trigger_cost_usd") or 0.0)
            + monitoring_cost_usd
        )
        record["updated_at"] = now_iso
        return record

    def record_alert_started(
        self,
        *,
        scope_id: Optional[str],
        user_id: Optional[str],
        alert_id: str,
        symbol: str,
        exchange: str,
        direction: str,
        started_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Start monitoring cost tracking for one alert."""
        normalized_scope_id = str(scope_id or "").strip()
        if not normalized_scope_id:
            return None

        timestamp = started_at or utc_now_iso()
        normalized_alert_id = str(alert_id or "").strip()
        normalized_symbol = str(symbol or "").upper().strip()
        normalized_exchange = str(exchange or "").lower().strip() or "unknown"

        record = self.db.get_scope(normalized_scope_id) or self._empty_record(
            scope_id=normalized_scope_id,
            user_id=user_id,
            timestamp=timestamp,
        )
        if user_id:
            record["user_id"] = user_id

        alerts = record.setdefault("alerts", {})
        existing = alerts.get(normalized_alert_id)
        if existing and existing.get("status") == "active":
            return self.db.upsert_scope(
                normalized_scope_id,
                self._recompute(record, now_iso=timestamp),
            )

        alerts[normalized_alert_id] = {
            "alert_id": normalized_alert_id,
            "scope_id": normalized_scope_id,
            "user_id": user_id,
            "symbol": normalized_symbol,
            "exchange": normalized_exchange,
            "direction": str(direction or "").upper().strip() or "LONG",
            "started_at": timestamp,
            "ended_at": None,
            "status": "active",
            "trigger_type": None,
            "trigger_price": None,
            "metadata": dict(metadata or {}),
        }

        record["alert_setup_count"] = int(record.get("alert_setup_count") or 0) + 1
        record["alert_setup_cost_usd"] = round_usd(
            float(record.get("alert_setup_cost_usd") or 0.0)
            + settings.ALERT_SETUP_COST_USD
        )

        symbols = record.setdefault("symbols", {})
        symbol_state = symbols.get(normalized_symbol) or {
            "symbol": normalized_symbol,
            "exchange": normalized_exchange,
            "closed_active_seconds": 0.0,
            "active_window_started_at": None,
            "active_alert_ids": [],
        }
        active_alert_ids = set(symbol_state.get("active_alert_ids", []))
        if not active_alert_ids and not symbol_state.get("active_window_started_at"):
            symbol_state["active_window_started_at"] = timestamp
        active_alert_ids.add(normalized_alert_id)
        symbol_state["active_alert_ids"] = sorted(active_alert_ids)
        symbols[normalized_symbol] = symbol_state

        return self.db.upsert_scope(
            normalized_scope_id,
            self._recompute(record, now_iso=timestamp),
        )

    def _close_alert(
        self,
        *,
        scope_id: Optional[str],
        alert_id: str,
        ended_at: Optional[str],
        status: str,
        trigger_type: Optional[str] = None,
        trigger_price: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        normalized_scope_id = str(scope_id or "").strip()
        if not normalized_scope_id:
            return None

        normalized_alert_id = str(alert_id or "").strip()
        if not normalized_alert_id:
            return None

        record = self.db.get_scope(normalized_scope_id)
        if not record:
            return None

        timestamp = ended_at or utc_now_iso()
        alerts = record.setdefault("alerts", {})
        alert = alerts.get(normalized_alert_id)
        if not alert or alert.get("status") != "active":
            return self.db.upsert_scope(
                normalized_scope_id,
                self._recompute(record, now_iso=timestamp),
            )

        alert["status"] = status
        alert["ended_at"] = timestamp
        alert["trigger_type"] = trigger_type
        alert["trigger_price"] = trigger_price

        symbol = alert.get("symbol")
        symbols = record.setdefault("symbols", {})
        symbol_state = symbols.get(symbol) or {}
        active_alert_ids = {
            item
            for item in symbol_state.get("active_alert_ids", [])
            if item != normalized_alert_id
        }
        symbol_state["active_alert_ids"] = sorted(active_alert_ids)
        active_window_started_at = symbol_state.get("active_window_started_at")
        if active_window_started_at and not active_alert_ids:
            closed_active_seconds = float(symbol_state.get("closed_active_seconds") or 0.0)
            closed_active_seconds += duration_seconds(active_window_started_at, timestamp)
            symbol_state["closed_active_seconds"] = closed_active_seconds
            symbol_state["active_window_started_at"] = None
        symbols[symbol] = symbol_state

        if status == "triggered":
            record["trigger_count"] = int(record.get("trigger_count") or 0) + 1
            record["trigger_cost_usd"] = round_usd(
                float(record.get("trigger_cost_usd") or 0.0)
                + settings.ALERT_TRIGGER_COST_USD
            )

        return self.db.upsert_scope(
            normalized_scope_id,
            self._recompute(record, now_iso=timestamp),
        )

    def record_alert_triggered(
        self,
        *,
        scope_id: Optional[str],
        alert_id: str,
        triggered_at: Optional[str] = None,
        trigger_type: Optional[str] = None,
        trigger_price: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """Finalize one alert after it triggered."""
        return self._close_alert(
            scope_id=scope_id,
            alert_id=alert_id,
            ended_at=triggered_at,
            status="triggered",
            trigger_type=trigger_type,
            trigger_price=trigger_price,
        )

    def record_alert_removed(
        self,
        *,
        scope_id: Optional[str],
        alert_id: str,
        removed_at: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Finalize one alert after manual removal."""
        return self._close_alert(
            scope_id=scope_id,
            alert_id=alert_id,
            ended_at=removed_at,
            status="removed",
        )

    def get_scope_summary(self, *, scope_id: str) -> Optional[Dict[str, Any]]:
        """Return one accumulated monitoring-cost summary with current active windows."""
        normalized_scope_id = str(scope_id or "").strip()
        if not normalized_scope_id:
            return None

        record = self.db.get_scope(normalized_scope_id)
        if not record:
            return None

        return self._recompute(record, now_iso=utc_now_iso())


_monitoring_cost_database: Optional[MonitoringCostDatabase] = None
_monitoring_cost_service: Optional[MonitoringCostService] = None


def get_monitoring_cost_database(
    db_path: Optional[str] = None,
) -> MonitoringCostDatabase:
    """Return the singleton monitoring-cost database."""
    global _monitoring_cost_database
    if _monitoring_cost_database is None:
        _monitoring_cost_database = MonitoringCostDatabase(db_path)
    return _monitoring_cost_database


def get_monitoring_cost_service() -> MonitoringCostService:
    """Return the singleton monitoring-cost service."""
    global _monitoring_cost_service
    if _monitoring_cost_service is None:
        _monitoring_cost_service = MonitoringCostService()
    return _monitoring_cost_service
