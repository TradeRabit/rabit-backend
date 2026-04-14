"""
Mem0 Client - User-specific memory management
Stores user preferences, trading limits, balance info, etc.
"""
from typing import Optional, List, Dict, Any
import aiohttp
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class Mem0Client:
    """
    Client for Mem0 user memory service
    
    Stores user-specific information like:
    - Trading balance limits
    - Risk preferences
    - Favorite assets
    - Trading strategies
    - Personal notes
    """
    
    def __init__(self):
        """Initialize Mem0 client"""
        self.enabled = settings.MEM0_ENABLED
        self.base_url = settings.MEM0_URL
        self.session: Optional[aiohttp.ClientSession] = None
        
        if self.enabled:
            logger.info(f"Mem0 client initialized: {self.base_url}")
        else:
            logger.info("Mem0 client disabled")
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def add_memory(
        self, 
        user_id: str, 
        text: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add memory for user
        
        Args:
            user_id: User ID
            text: Memory text (e.g., "My trading balance limit is $10,000")
            metadata: Optional metadata
            
        Returns:
            Memory creation result
        """
        if not self.enabled:
            logger.warning("Mem0 is disabled")
            return {"success": False, "error": "Mem0 is disabled"}
        
        try:
            await self._ensure_session()
            
            payload = {
                "user_id": user_id,
                "text": text,
                "metadata": metadata or {}
            }
            
            async with self.session.post(
                f"{self.base_url}/memories",
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Added memory for user {user_id}")
                    return {"success": True, "data": result}
                else:
                    error = await response.text()
                    logger.error(f"Error adding memory: {error}")
                    return {"success": False, "error": error}
        
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return {"success": False, "error": str(e)}
    
    async def search_memories(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search memories for user
        
        Args:
            user_id: User ID
            query: Search query (e.g., "trading balance")
            limit: Maximum number of results
            
        Returns:
            List of matching memories
        """
        if not self.enabled:
            logger.warning("Mem0 is disabled")
            return []
        
        try:
            await self._ensure_session()
            
            params = {
                "user_id": user_id,
                "query": query,
                "limit": limit
            }
            
            async with self.session.get(
                f"{self.base_url}/memories/search",
                params=params
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug(f"Found {len(result)} memories for user {user_id}")
                    return result
                else:
                    logger.error(f"Error searching memories: {response.status}")
                    return []
        
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    async def get_all_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all memories for user
        
        Args:
            user_id: User ID
            
        Returns:
            List of all memories
        """
        if not self.enabled:
            logger.warning("Mem0 is disabled")
            return []
        
        try:
            await self._ensure_session()
            
            async with self.session.get(
                f"{self.base_url}/memories",
                params={"user_id": user_id}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug(f"Retrieved {len(result)} memories for user {user_id}")
                    return result
                else:
                    logger.error(f"Error getting memories: {response.status}")
                    return []
        
        except Exception as e:
            logger.error(f"Error getting memories: {e}")
            return []
    
    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """
        Delete specific memory
        
        Args:
            user_id: User ID
            memory_id: Memory ID to delete
            
        Returns:
            True if successful
        """
        if not self.enabled:
            logger.warning("Mem0 is disabled")
            return False
        
        try:
            await self._ensure_session()
            
            async with self.session.delete(
                f"{self.base_url}/memories/{memory_id}",
                params={"user_id": user_id}
            ) as response:
                if response.status == 200:
                    logger.info(f"Deleted memory {memory_id} for user {user_id}")
                    return True
                else:
                    logger.error(f"Error deleting memory: {response.status}")
                    return False
        
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False
    
    async def delete_all_memories(self, user_id: str) -> bool:
        """
        Delete all memories for user
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful
        """
        if not self.enabled:
            logger.warning("Mem0 is disabled")
            return False
        
        try:
            await self._ensure_session()
            
            async with self.session.delete(
                f"{self.base_url}/memories",
                params={"user_id": user_id}
            ) as response:
                if response.status == 200:
                    logger.info(f"Deleted all memories for user {user_id}")
                    return True
                else:
                    logger.error(f"Error deleting memories: {response.status}")
                    return False
        
        except Exception as e:
            logger.error(f"Error deleting memories: {e}")
            return False
    
    async def get_context(self, user_id: str, query: str) -> str:
        """
        Get relevant context for query
        
        Args:
            user_id: User ID
            query: Query to get context for
            
        Returns:
            Context string with relevant memories
        """
        memories = await self.search_memories(user_id, query, limit=5)
        
        if not memories:
            return ""
        
        context_parts = []
        for memory in memories:
            text = memory.get("text", "")
            if text:
                context_parts.append(f"- {text}")
        
        if context_parts:
            return "User Information:\n" + "\n".join(context_parts)
        
        return ""


# Singleton instance
_mem0_client: Optional[Mem0Client] = None


def get_mem0_client() -> Mem0Client:
    """Get or create Mem0Client singleton"""
    global _mem0_client
    if _mem0_client is None:
        _mem0_client = Mem0Client()
    return _mem0_client
