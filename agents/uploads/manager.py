"""Temporary file upload manager for multimodal agent inputs."""
import json
import mimetypes
import uuid
from pathlib import Path
from typing import Dict, Iterable, Optional

from fastapi import UploadFile

from config.settings import settings
from utils.logger import get_logger

from .models import AgentAttachment, AttachmentKind, UploadedFileRecord

logger = get_logger(__name__)

IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
DOCUMENT_CONTENT_TYPES = {"application/pdf"}
SUPPORTED_CONTENT_TYPES = IMAGE_CONTENT_TYPES | DOCUMENT_CONTENT_TYPES


class UploadValidationError(ValueError):
    """Raised when an uploaded file does not pass validation."""


class TemporaryUploadManager:
    """Manages temporary files and metadata for multimodal agent requests."""

    def __init__(
        self,
        storage_dir: Path | str | None = None,
        ttl_seconds: Optional[int] = None,
        max_size_mb: Optional[int] = None,
    ):
        self.storage_dir = Path(storage_dir or settings.AGENT_UPLOAD_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.storage_dir / "index.json"
        self.ttl_seconds = ttl_seconds or settings.AGENT_UPLOAD_TTL_SECONDS
        self.max_size_bytes = (max_size_mb or settings.AGENT_UPLOAD_MAX_SIZE_MB) * 1024 * 1024
        self._index: Dict[str, UploadedFileRecord] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load persisted upload metadata from disk."""
        if not self.index_path.exists():
            self._index = {}
            return

        try:
            raw_index = json.loads(self.index_path.read_text(encoding="utf-8"))
            self._index = {
                file_id: UploadedFileRecord(**record)
                for file_id, record in raw_index.items()
            }
        except Exception as exc:
            logger.error(f"Failed to load upload index: {exc}")
            self._index = {}

    def _save_index(self) -> None:
        """Persist upload metadata to disk."""
        serialized = {
            file_id: record.model_dump(mode="json")
            for file_id, record in self._index.items()
        }
        self.index_path.write_text(
            json.dumps(serialized, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def cleanup_expired(self) -> int:
        """Delete expired files and return the number removed."""
        removed = 0

        for file_id in list(self._index):
            record = self._index[file_id]
            if not record.is_expired:
                continue
            self._delete_record(record)
            removed += 1

        if removed:
            self._save_index()

        return removed

    def delete(self, file_id: str) -> bool:
        """Delete an uploaded file by ID."""
        record = self._index.get(file_id)
        if not record:
            return False

        self._delete_record(record)
        self._save_index()
        return True

    def get_record(self, file_id: str) -> Optional[UploadedFileRecord]:
        """Fetch an upload record if it still exists and is not expired."""
        record = self._index.get(file_id)
        if not record:
            return None

        if record.is_expired:
            self._delete_record(record)
            self._save_index()
            return None

        file_path = self.storage_dir / record.stored_filename
        if not file_path.exists():
            logger.warning(f"Upload file missing on disk for file_id={file_id}")
            del self._index[file_id]
            self._save_index()
            return None

        return record

    def resolve_attachments(self, file_ids: Iterable[str]) -> list[AgentAttachment]:
        """Resolve uploaded file IDs into local attachments for the model call."""
        attachments: list[AgentAttachment] = []

        for file_id in file_ids:
            record = self.get_record(file_id)
            if not record:
                raise UploadValidationError(f"Attachment '{file_id}' not found or expired")

            file_path = self.storage_dir / record.stored_filename
            attachments.append(
                AgentAttachment(
                    file_id=record.file_id,
                    filename=record.original_filename,
                    content_type=record.content_type,
                    kind=record.kind,
                    path=str(file_path),
                    size_bytes=record.size_bytes,
                )
            )

        return attachments

    async def save_upload(self, upload: UploadFile) -> UploadedFileRecord:
        """Validate and store an uploaded file."""
        self.cleanup_expired()

        filename = upload.filename or "upload"
        content_type = upload.content_type or mimetypes.guess_type(filename)[0] or ""
        content_type = content_type.lower()

        if content_type not in SUPPORTED_CONTENT_TYPES:
            raise UploadValidationError(
                f"Unsupported content type '{content_type}'. "
                "Supported types: image/jpeg, image/png, image/webp, application/pdf"
            )

        contents = await upload.read()
        size_bytes = len(contents)

        if not contents:
            raise UploadValidationError("Uploaded file is empty")

        if size_bytes > self.max_size_bytes:
            raise UploadValidationError(
                f"Uploaded file exceeds {self.max_size_bytes // (1024 * 1024)} MB limit"
            )

        file_id = uuid.uuid4().hex
        suffix = Path(filename).suffix or self._guess_extension(content_type)
        stored_filename = f"{file_id}{suffix}"
        target_path = self.storage_dir / stored_filename
        target_path.write_bytes(contents)

        kind: AttachmentKind = "document" if content_type in DOCUMENT_CONTENT_TYPES else "image"
        record = UploadedFileRecord.with_ttl(
            file_id=file_id,
            original_filename=filename,
            stored_filename=stored_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            kind=kind,
            ttl_seconds=self.ttl_seconds,
        )

        self._index[file_id] = record
        self._save_index()
        return record

    def _guess_extension(self, content_type: str) -> str:
        """Map supported content types to a stable filename extension."""
        mapping = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "application/pdf": ".pdf",
        }
        return mapping.get(content_type, "")

    def _delete_record(self, record: UploadedFileRecord) -> None:
        """Delete a record and its backing file if present."""
        file_path = self.storage_dir / record.stored_filename
        if file_path.exists():
            file_path.unlink()

        self._index.pop(record.file_id, None)


_upload_manager: Optional[TemporaryUploadManager] = None


def get_upload_manager() -> TemporaryUploadManager:
    """Return the singleton temporary upload manager."""
    global _upload_manager
    if _upload_manager is None:
        _upload_manager = TemporaryUploadManager()
    return _upload_manager

