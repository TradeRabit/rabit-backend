"""Tool functions for Mem0-backed long-term memory."""
import json
from typing import Any, Dict, Optional

from agents.memory import get_mem0_client
from agents.tools.core.runtime_context import get_current_user_id
from config.settings import settings


def _ensure_memory_tools_enabled() -> None:
    """Ensure memory tools are enabled by configuration."""
    if not settings.MEMORY_TOOLS_ENABLED:
        raise ValueError("Memory tools are disabled by configuration")


def _require_user_id() -> str:
    """Ensure a tool is running inside a user-scoped agent request."""
    _ensure_memory_tools_enabled()
    user_id = get_current_user_id()
    if not user_id:
        raise ValueError("No active user_id is available for memory tools")
    return user_id


def _parse_metadata(metadata_json: Optional[str], category: Optional[str]) -> Dict[str, Any]:
    """Parse optional metadata values supplied by the model."""
    metadata: Dict[str, Any] = {}

    if metadata_json:
        parsed = json.loads(metadata_json)
        if not isinstance(parsed, dict):
            raise ValueError("metadata_json must decode to an object")
        metadata.update(parsed)

    if category:
        metadata["category"] = category

    return metadata


async def add_user_memory(
    text: str,
    category: Optional[str] = None,
    metadata_json: Optional[str] = None,
) -> Dict[str, Any]:
    """Persist a long-term memory for the active user."""
    user_id = _require_user_id()
    metadata = _parse_metadata(metadata_json, category)
    result = await get_mem0_client().add_memory(
        user_id=user_id,
        text=text,
        metadata=metadata or None,
    )
    return {
        "success": True,
        "user_id": user_id,
        "result": result,
    }


async def get_user_memory(
    query: Optional[str] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    """List or search the active user's memories."""
    user_id = _require_user_id()
    client = get_mem0_client()

    if query:
        memories = await client.search_memories(user_id=user_id, query=query, limit=limit)
    else:
        memories = await client.get_all_memories(user_id=user_id)
        memories = memories[:limit]

    return {
        "user_id": user_id,
        "query": query,
        "memories": memories,
        "total": len(memories),
    }


async def delete_user_memory(memory_id: str) -> Dict[str, Any]:
    """Delete one memory for the active user."""
    user_id = _require_user_id()
    await get_mem0_client().delete_memory(user_id=user_id, memory_id=memory_id)
    return {
        "success": True,
        "user_id": user_id,
        "memory_id": memory_id,
    }


async def clear_user_memories() -> Dict[str, Any]:
    """Delete every long-term memory for the active user."""
    user_id = _require_user_id()
    await get_mem0_client().delete_all_memories(user_id=user_id)
    return {
        "success": True,
        "user_id": user_id,
        "deleted_all": True,
    }
