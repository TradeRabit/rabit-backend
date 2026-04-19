"""Session-scoped pipeline artifact persistence."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def utc_now() -> datetime:
    """Return the current aware UTC datetime."""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Return the current aware UTC datetime as ISO text."""
    return utc_now().isoformat()


def _is_expired(record: Dict[str, Any], *, now: Optional[datetime] = None) -> bool:
    """Return whether one artifact record is expired."""
    expires_at = str(record.get("expires_at") or "").strip()
    if not expires_at:
        return False
    try:
        parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed <= (now or utc_now())
    except ValueError:
        return False


class AgentPipelineArtifactDatabase:
    """Lightweight JSON-backed store for pipeline artifacts grouped by scope."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.AGENT_PIPELINE_ARTIFACTS_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self.data: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Load stored pipeline artifacts from disk."""
        with self._lock:
            if not self.db_path.exists():
                self.data = {}
                logger.info("Agent pipeline artifact database file not found, starting fresh")
                return

            try:
                with open(self.db_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                self.data = payload if isinstance(payload, dict) else {}
                logger.info("Loaded %s pipeline artifact scopes from database", len(self.data))
            except Exception as exc:
                logger.error("Error loading pipeline artifact database: %s", exc)
                self.data = {}

    def save(self) -> None:
        """Persist pipeline artifacts to disk."""
        with self._lock:
            with open(self.db_path, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, ensure_ascii=False, default=str)

    def cleanup_expired(self) -> int:
        """Delete expired artifacts and return the number removed."""
        removed = 0
        now = utc_now()
        with self._lock:
            for scope_id in list(self.data.keys()):
                scope_record = self.data.get(scope_id) or {}
                artifacts = scope_record.get("artifacts", [])
                if not isinstance(artifacts, list):
                    artifacts = []
                kept = [record for record in artifacts if not _is_expired(record, now=now)]
                removed += max(0, len(artifacts) - len(kept))
                if kept:
                    scope_record["artifacts"] = kept
                    scope_record["updated_at"] = now.isoformat()
                    self.data[scope_id] = scope_record
                else:
                    self.data.pop(scope_id, None)

            if removed:
                self.save()
        return removed

    def get_scope(self, scope_id: str) -> Optional[Dict[str, Any]]:
        """Return one stored scope artifact summary if present."""
        with self._lock:
            record = self.data.get(scope_id)
            return dict(record) if record else None

    def upsert_scope(self, scope_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Create or replace one scope artifact summary."""
        with self._lock:
            self.data[scope_id] = dict(record)
            self.save()
            return dict(self.data[scope_id])


class AgentPipelineArtifactService:
    """Persist and retrieve session-scoped pipeline artifacts."""

    def __init__(
        self,
        db: Optional[AgentPipelineArtifactDatabase] = None,
        *,
        ttl_seconds: Optional[int] = None,
    ):
        self.db = db or get_pipeline_artifact_database()
        self.ttl_seconds = int(ttl_seconds or settings.AGENT_PIPELINE_ARTIFACT_TTL_SECONDS)

    def record_artifact(
        self,
        *,
        scope_id: str,
        user_id: Optional[str],
        node_name: str,
        kind: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Persist one pipeline artifact and return the normalized record."""
        normalized_scope_id = str(scope_id or "").strip()
        if not normalized_scope_id:
            raise ValueError("scope_id is required for pipeline artifact persistence.")

        self.db.cleanup_expired()
        timestamp = utc_now()
        record = self.db.get_scope(normalized_scope_id) or {
            "scope_id": normalized_scope_id,
            "user_id": user_id,
            "artifacts": [],
            "created_at": timestamp.isoformat(),
            "updated_at": timestamp.isoformat(),
        }
        if user_id:
            record["user_id"] = user_id

        artifact = {
            "artifact_id": uuid.uuid4().hex,
            "scope_id": normalized_scope_id,
            "user_id": user_id,
            "node_name": str(node_name or "").strip(),
            "kind": str(kind or "generic").strip(),
            "payload": dict(payload or {}),
            "metadata": dict(metadata or {}),
            "created_at": timestamp.isoformat(),
            "expires_at": (timestamp + timedelta(seconds=self.ttl_seconds)).isoformat(),
        }
        artifacts = list(record.get("artifacts", []))
        artifacts.append(artifact)
        record["artifacts"] = artifacts
        record["updated_at"] = timestamp.isoformat()
        self.db.upsert_scope(normalized_scope_id, record)
        return artifact

    def list_scope_artifacts(self, *, scope_id: str) -> Optional[Dict[str, Any]]:
        """Return one normalized scope artifact summary."""
        normalized_scope_id = str(scope_id or "").strip()
        if not normalized_scope_id:
            return None

        self.db.cleanup_expired()
        record = self.db.get_scope(normalized_scope_id)
        if not record:
            return None

        artifacts = record.get("artifacts", [])
        if not isinstance(artifacts, list):
            artifacts = []
        record["artifacts"] = sorted(
            artifacts,
            key=lambda item: str(item.get("created_at") or ""),
            reverse=True,
        )
        return record


_pipeline_artifact_database: Optional[AgentPipelineArtifactDatabase] = None
_pipeline_artifact_service: Optional[AgentPipelineArtifactService] = None


def get_pipeline_artifact_database(
    db_path: Optional[str] = None,
) -> AgentPipelineArtifactDatabase:
    """Return the singleton pipeline artifact database."""
    global _pipeline_artifact_database
    if _pipeline_artifact_database is None:
        _pipeline_artifact_database = AgentPipelineArtifactDatabase(db_path)
    return _pipeline_artifact_database


def get_pipeline_artifact_service() -> AgentPipelineArtifactService:
    """Return the singleton pipeline artifact service."""
    global _pipeline_artifact_service
    if _pipeline_artifact_service is None:
        _pipeline_artifact_service = AgentPipelineArtifactService()
    return _pipeline_artifact_service
