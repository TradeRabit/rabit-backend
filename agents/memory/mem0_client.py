"""Mem0 client for self-hosted long-term user memory."""
import logging
from typing import Any, Dict, List, Optional, Sequence

import aiohttp

from config.settings import settings

logger = logging.getLogger(__name__)


class Mem0Error(RuntimeError):
    """Base Mem0 client error."""


class Mem0DisabledError(Mem0Error):
    """Raised when Mem0 integration is disabled."""


class Mem0RequestError(Mem0Error):
    """Raised when the Mem0 service request fails."""


class Mem0Client:
    """Client wrapper around the Mem0 OSS REST API."""

    def __init__(
        self,
        *,
        enabled: Optional[bool] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.enabled = settings.MEM0_ENABLED if enabled is None else enabled
        self.base_url = (base_url or settings.MEM0_URL).rstrip("/")
        self.api_key = settings.MEM0_API_KEY if api_key is None else api_key
        self.session: Optional[aiohttp.ClientSession] = None

        if self.enabled:
            logger.info(f"Mem0 client initialized: {self.base_url}")
        else:
            logger.info("Mem0 client disabled")

    async def _ensure_session(self) -> None:
        """Ensure an aiohttp session exists."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    def _headers(self) -> Dict[str, str]:
        """Build request headers for Mem0 API calls."""
        headers: Dict[str, str] = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def _ensure_enabled(self) -> None:
        """Raise if Mem0 is disabled."""
        if not self.enabled:
            raise Mem0DisabledError("Mem0 is disabled")

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        expected_statuses: Sequence[int] = (200,),
    ) -> Any:
        """Perform a Mem0 request and return the decoded response body."""
        self._ensure_enabled()
        await self._ensure_session()

        url = f"{self.base_url}{path}"
        assert self.session is not None  # Narrow for type-checkers.

        async with self.session.request(
            method,
            url,
            params=params,
            json=json,
            headers=self._headers(),
        ) as response:
            if response.status not in expected_statuses:
                body = await response.text()
                raise Mem0RequestError(
                    f"Mem0 {method} {path} failed with status {response.status}: {body}"
                )

            if response.status == 204:
                return None

            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return await response.json()
            return await response.text()

    def _extract_items(self, payload: Any) -> List[Dict[str, Any]]:
        """Normalize list-like Mem0 responses into a plain list."""
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]

        if not isinstance(payload, dict):
            return []

        for key in ("results", "memories", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

        data = payload.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            for key in ("results", "memories", "items"):
                value = data.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]

        return []

    def _extract_text(self, memory: Dict[str, Any]) -> str:
        """Read the user-facing text from a memory object."""
        for key in ("memory", "text", "content"):
            value = memory.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    async def health_check(self) -> Dict[str, Any]:
        """Check whether the Mem0 service is reachable."""
        self._ensure_enabled()
        await self._ensure_session()
        assert self.session is not None

        async with self.session.get(
            f"{self.base_url}/",
            headers=self._headers(),
        ) as response:
            body = await response.text()
            if response.status >= 500:
                raise Mem0RequestError(
                    f"Mem0 health check failed with status {response.status}: {body}"
                )

            return {
                "healthy": True,
                "status_code": response.status,
                "body": body,
            }

    async def add_memory(
        self,
        user_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add a user memory via the Mem0 OSS API."""
        payload: Dict[str, Any] = {
            "messages": [{"role": "user", "content": text}],
            "user_id": user_id,
        }
        if metadata:
            payload["metadata"] = metadata

        result = await self._request(
            "POST",
            "/memories",
            json=payload,
            expected_statuses=(200, 201),
        )
        logger.info(f"Added memory for user {user_id}")
        return result if isinstance(result, dict) else {"result": result}

    async def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for relevant memories by semantic query."""
        payload = {
            "query": query,
            "user_id": user_id,
            "limit": limit,
        }
        result = await self._request(
            "POST",
            "/search",
            json=payload,
            expected_statuses=(200,),
        )
        memories = self._extract_items(result)
        logger.debug(f"Found {len(memories)} memories for user {user_id}")
        return memories

    async def get_all_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Return all memories stored for a user."""
        result = await self._request(
            "GET",
            "/memories",
            params={"user_id": user_id},
            expected_statuses=(200,),
        )
        memories = self._extract_items(result)
        logger.debug(f"Retrieved {len(memories)} memories for user {user_id}")
        return memories

    async def get_memory(self, user_id: str, memory_id: str) -> Dict[str, Any]:
        """Return one memory by ID."""
        result = await self._request(
            "GET",
            f"/memories/{memory_id}",
            params={"user_id": user_id},
            expected_statuses=(200,),
        )
        if isinstance(result, dict):
            return result
        return {"memory": result}

    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete one memory by ID."""
        await self._request(
            "DELETE",
            f"/memories/{memory_id}",
            params={"user_id": user_id},
            expected_statuses=(200, 204),
        )
        logger.info(f"Deleted memory {memory_id} for user {user_id}")
        return True

    async def delete_all_memories(self, user_id: str) -> bool:
        """Delete every memory for a user."""
        await self._request(
            "DELETE",
            "/memories",
            params={"user_id": user_id},
            expected_statuses=(200, 204),
        )
        logger.info(f"Deleted all memories for user {user_id}")
        return True

    async def get_context(self, user_id: str, query: str) -> str:
        """Build a compact context string for the current query."""
        memories = await self.search_memories(user_id, query, limit=5)
        if not memories:
            return ""

        lines = []
        for memory in memories:
            text = self._extract_text(memory)
            if text:
                lines.append(f"- {text}")

        if not lines:
            return ""

        return "Relevant long-term user memory:\n" + "\n".join(lines)


_mem0_client: Optional[Mem0Client] = None


def get_mem0_client() -> Mem0Client:
    """Return the singleton Mem0 client."""
    global _mem0_client
    if _mem0_client is None:
        _mem0_client = Mem0Client()
    return _mem0_client
