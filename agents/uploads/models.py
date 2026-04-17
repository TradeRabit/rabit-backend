"""Models for temporary multimodal agent uploads."""
from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field


AttachmentKind = Literal["image", "document"]


class UploadedFileRecord(BaseModel):
    """Persistent metadata for a temporary uploaded file."""

    file_id: str
    original_filename: str
    stored_filename: str
    content_type: str
    size_bytes: int
    kind: AttachmentKind
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        """Return whether the record is already expired."""
        return self.expires_at <= datetime.utcnow()

    @classmethod
    def with_ttl(
        cls,
        *,
        file_id: str,
        original_filename: str,
        stored_filename: str,
        content_type: str,
        size_bytes: int,
        kind: AttachmentKind,
        ttl_seconds: int,
    ) -> "UploadedFileRecord":
        """Create a record with an expiry derived from TTL seconds."""
        return cls(
            file_id=file_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            kind=kind,
            expires_at=datetime.utcnow() + timedelta(seconds=ttl_seconds),
        )


class AgentAttachment(BaseModel):
    """Resolved attachment used by the runtime agent pipeline."""

    file_id: str
    filename: str
    content_type: str
    kind: AttachmentKind
    path: str
    size_bytes: int

