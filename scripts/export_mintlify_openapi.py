"""Export the FastAPI OpenAPI schema for Mintlify API reference pages."""
from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from main import app


OUTPUT_PATH = REPO_ROOT / ".doch" / "api-reference" / "openapi.json"


TAG_METADATA = [
    {
        "name": "System",
        "description": "Platform metadata and backend health endpoints.",
    },
    {
        "name": "Auth",
        "description": "Wallet authentication, nonce generation, verification, and current identity.",
    },
    {
        "name": "Agent",
        "description": "Multimodal uploads, chat, and SSE streaming chat endpoints.",
    },
    {
        "name": "Memory",
        "description": "Mem0-backed memory health and CRUD/search behavior.",
    },
    {
        "name": "Exchange Connections",
        "description": "Execution access state and Backpack credential management.",
    },
    {
        "name": "Drift",
        "description": "Same-wallet Drift execution prepare and submit flow.",
    },
    {
        "name": "Assets",
        "description": "Asset lookup, categories, summaries, trending, related assets, and OHLC.",
    },
    {
        "name": "Models",
        "description": "OpenRouter model catalog, model database operations, and accumulated session cost.",
    },
]


def convert_nullable_anyof(node):
    """Convert FastAPI nullable unions into OpenAPI 3.0 nullable schemas."""
    if isinstance(node, dict):
        any_of = node.get("anyOf")
        if isinstance(any_of, list) and len(any_of) == 2:
            non_null = None
            has_null = False
            for item in any_of:
                if isinstance(item, dict) and item.get("type") == "null":
                    has_null = True
                else:
                    non_null = item
            if has_null and isinstance(non_null, dict):
                merged = dict(non_null)
                for key, value in node.items():
                    if key != "anyOf":
                        merged[key] = value
                merged["nullable"] = True
                node.clear()
                node.update(merged)

        for value in list(node.values()):
            convert_nullable_anyof(value)
    elif isinstance(node, list):
        for item in node:
            convert_nullable_anyof(item)


def normalize_binary_upload_schemas(node):
    """Convert FastAPI file-upload schemas into OpenAPI 3.0 binary format."""
    if isinstance(node, dict):
        if node.get("type") == "string" and node.get("contentMediaType"):
            node["format"] = "binary"
            node.pop("contentMediaType", None)
            node.pop("contentEncoding", None)

        for value in list(node.values()):
            normalize_binary_upload_schemas(value)
    elif isinstance(node, list):
        for item in node:
            normalize_binary_upload_schemas(item)


def normalize_tags(schema: dict) -> None:
    """Normalize tag names so Mintlify groups the API cleanly."""
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            tags = operation.get("tags", [])
            normalized = []
            for tag in tags:
                if tag == "Chart Data":
                    normalized.append("Assets")
                elif tag == "Root":
                    normalized.append("System")
                else:
                    normalized.append(tag)
            if normalized:
                operation["tags"] = normalized


def build_schema() -> dict:
    """Build the normalized OpenAPI schema for Mintlify."""
    app.openapi_version = "3.0.3"
    app.openapi_schema = None
    schema = app.openapi()
    convert_nullable_anyof(schema)
    normalize_binary_upload_schemas(schema)
    normalize_tags(schema)

    schema["info"]["title"] = "Rabit Backend API"
    schema["info"]["description"] = (
        "REST and streaming API for the Rabit trading assistant backend."
    )
    schema["tags"] = TAG_METADATA
    schema["servers"] = [
        {"url": "http://localhost:8000", "description": "Local development"},
    ]
    return schema


def main() -> None:
    schema = build_schema()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Exported Mintlify OpenAPI schema to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
