import asyncio
import io
from pathlib import Path

from fastapi import UploadFile
from starlette.datastructures import Headers

from agents.uploads import TemporaryUploadManager, UploadValidationError


def make_upload(filename: str, content_type: str, payload: bytes) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=io.BytesIO(payload),
        headers=Headers({"content-type": content_type}),
    )


def test_upload_manager_saves_resolves_and_deletes(tmp_path: Path):
    manager = TemporaryUploadManager(storage_dir=tmp_path, ttl_seconds=3600, max_size_mb=1)

    record = asyncio.run(
        manager.save_upload(make_upload("chart.png", "image/png", b"fake-image-data"))
    )

    assert record.original_filename == "chart.png"
    assert record.content_type == "image/png"
    assert (tmp_path / record.stored_filename).exists()

    attachments = manager.resolve_attachments([record.file_id])
    assert len(attachments) == 1
    assert attachments[0].filename == "chart.png"
    assert attachments[0].kind == "image"

    assert manager.delete(record.file_id) is True
    assert manager.get_record(record.file_id) is None


def test_upload_manager_rejects_unsupported_content_type(tmp_path: Path):
    manager = TemporaryUploadManager(storage_dir=tmp_path, ttl_seconds=3600, max_size_mb=1)

    try:
        asyncio.run(
            manager.save_upload(make_upload("notes.txt", "text/plain", b"hello"))
        )
    except UploadValidationError as exc:
        assert "Unsupported content type" in str(exc)
    else:
        raise AssertionError("Expected UploadValidationError for text/plain")

