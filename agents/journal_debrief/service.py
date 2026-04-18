"""Service layer for structured trade debrief persistence."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from .database import get_trade_debrief_database, utc_now_iso


def _normalize_optional_text(value: Optional[str]) -> Optional[str]:
    normalized = str(value or "").strip()
    return normalized or None


class TradeDebriefService:
    """Manage structured trade debrief records for users."""

    def __init__(self, db=None):
        self.db = db or get_trade_debrief_database()

    def create_entry(
        self,
        *,
        user_id: str,
        summary: str,
        exchange: Optional[str] = None,
        symbol: Optional[str] = None,
        side: Optional[str] = None,
        entry_price: Optional[float] = None,
        exit_price: Optional[float] = None,
        pnl: Optional[float] = None,
        lesson: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create and persist one structured trade debrief entry."""
        normalized_summary = str(summary or "").strip()
        if not user_id:
            raise ValueError("user_id is required for trade debrief entries.")
        if not normalized_summary:
            raise ValueError("summary is required for trade debrief entries.")

        normalized_exchange = _normalize_optional_text(exchange)
        if normalized_exchange:
            normalized_exchange = normalized_exchange.lower()
        normalized_symbol = _normalize_optional_text(symbol)
        if normalized_symbol:
            normalized_symbol = normalized_symbol.upper()
        normalized_side = _normalize_optional_text(side)
        if normalized_side:
            normalized_side = normalized_side.lower()

        computed_pnl = pnl
        if computed_pnl is None and entry_price is not None and exit_price is not None:
            if normalized_side in {"short", "sell"}:
                computed_pnl = float(entry_price) - float(exit_price)
            else:
                computed_pnl = float(exit_price) - float(entry_price)

        pnl_percent = None
        if computed_pnl is not None and entry_price not in {None, 0}:
            pnl_percent = (float(computed_pnl) / float(entry_price)) * 100.0

        outcome = "flat"
        if computed_pnl is not None:
            if computed_pnl > 0:
                outcome = "win"
            elif computed_pnl < 0:
                outcome = "loss"

        normalized_tags = sorted(
            {
                str(tag).strip().lower()
                for tag in (tags or [])
                if str(tag).strip()
            }
        )

        record = {
            "id": f"debrief_{uuid4().hex[:12]}",
            "user_id": user_id,
            "summary": normalized_summary,
            "exchange": normalized_exchange,
            "symbol": normalized_symbol,
            "side": normalized_side,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": computed_pnl,
            "pnl_percent": pnl_percent,
            "outcome": outcome,
            "lesson": _normalize_optional_text(lesson),
            "notes": _normalize_optional_text(notes),
            "tags": normalized_tags,
            "created_at": utc_now_iso(),
        }
        return self.db.upsert_entry(record)

    def list_entries(
        self,
        *,
        user_id: str,
        symbol: Optional[str] = None,
        exchange: Optional[str] = None,
        limit: Optional[int] = 20,
    ) -> List[Dict[str, Any]]:
        """List one user's stored trade debrief entries."""
        if not user_id:
            raise ValueError("user_id is required for trade debrief entries.")
        return self.db.list_entries(
            user_id=user_id,
            symbol=symbol,
            exchange=exchange,
            limit=limit,
        )


_trade_debrief_service: Optional[TradeDebriefService] = None


def get_trade_debrief_service() -> TradeDebriefService:
    """Return singleton trade debrief service."""
    global _trade_debrief_service
    if _trade_debrief_service is None:
        _trade_debrief_service = TradeDebriefService()
    return _trade_debrief_service
