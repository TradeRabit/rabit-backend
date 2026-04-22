"""
Persistent database for conversation sessions
Stores conversation history to survive server restarts
"""
import json
import os
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
import logging

from agents.memory.conversation import Message

logger = logging.getLogger(__name__)


class ConversationDatabase:
    """
    JSON-based database for conversation persistence
    Stores conversations permanently to survive server restarts
    """
    
    def __init__(self, db_path: str = "data/conversations.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Dict] = {}
        self.load()
        
    def load(self):
        """Load database from file"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info(f"Loaded {len(self.data)} conversation sessions from database")
            except Exception as e:
                logger.error(f"Error loading conversation database: {e}")
                self.data = {}
        else:
            logger.info("Conversation database file not found, starting fresh")
            self.data = {}
    
    def save(self):
        """Save database to file"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False, default=str)
            logger.debug(f"Saved {len(self.data)} conversation sessions to database")
        except Exception as e:
            logger.error(f"Error saving conversation database: {e}")
    
    def save_session(self, scope_id: str, messages: List[Message], metadata: Optional[Dict] = None):
        """
        Save conversation session
        
        Args:
            scope_id: Session scope ID (e.g., "global", "asset:BTC")
            messages: List of messages in the conversation
            metadata: Optional metadata (title, created_at, etc.)
        """
        try:
            existing_metadata = dict(self.data.get(scope_id, {}).get("metadata", {}) or {})
            merged_metadata = {
                **existing_metadata,
                **(metadata or {}),
            }
            session_data = {
                "scope_id": scope_id,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat()
                    }
                    for msg in messages
                ],
                "metadata": merged_metadata,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Create session if not exists
            if scope_id not in self.data:
                session_data["metadata"]["created_at"] = datetime.utcnow().isoformat()
            else:
                # Preserve created_at
                if "created_at" in self.data[scope_id].get("metadata", {}):
                    session_data["metadata"]["created_at"] = self.data[scope_id]["metadata"]["created_at"]
            
            self.data[scope_id] = session_data
            self.save()
            logger.debug(f"Saved session: {scope_id} ({len(messages)} messages)")
        except Exception as e:
            logger.error(f"Error saving session {scope_id}: {e}")
    
    def load_session(self, scope_id: str) -> Optional[List[Message]]:
        """
        Load conversation session
        
        Args:
            scope_id: Session scope ID
            
        Returns:
            List of messages or None if not found
        """
        if scope_id not in self.data:
            return None
        
        try:
            session_data = self.data[scope_id]
            messages = []
            
            for msg_data in session_data.get("messages", []):
                message = Message(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"])
                )
                messages.append(message)
            
            logger.debug(f"Loaded session: {scope_id} ({len(messages)} messages)")
            return messages
        except Exception as e:
            logger.error(f"Error loading session {scope_id}: {e}")
            return None
    
    def delete_session(self, scope_id: str):
        """Delete conversation session"""
        if scope_id in self.data:
            del self.data[scope_id]
            self.save()
            logger.info(f"Deleted session: {scope_id}")

    def get_session_record(self, scope_id: str) -> Optional[Dict]:
        """Return the raw stored session payload."""
        session = self.data.get(scope_id)
        if session is None:
            return None
        return dict(session)

    def build_session_summary(self, scope_id: str, session_data: Dict) -> Dict:
        """Build one consistent session summary dict."""
        metadata = session_data.get("metadata", {}) or {}
        messages = session_data.get("messages", []) or []

        title = metadata.get("title")
        if not title and messages:
            for msg in messages:
                if msg.get("role") == "user":
                    content = str(msg.get("content") or "")
                    title = content[:50] + ("..." if len(content) > 50 else "")
                    break

        return {
            "scope_id": scope_id,
            "title": title or "Untitled",
            "message_count": len(messages),
            "created_at": metadata.get("created_at"),
            "updated_at": session_data.get("updated_at"),
            "last_message": str(messages[-1].get("content") or "")[:100] if messages else None,
            "user_id": metadata.get("user_id"),
            "scope_mode": metadata.get("scope_mode"),
            "symbol": metadata.get("symbol"),
            "exchange": metadata.get("exchange"),
            "source_screen": metadata.get("source_screen"),
        }

    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict]:
        """
        List all conversation sessions
        
        Returns:
            List of session summaries
        """
        sessions = []
        for scope_id, session_data in self.data.items():
            summary = self.build_session_summary(scope_id, session_data)
            if user_id and summary.get("user_id") != user_id:
                continue
            sessions.append(summary)
        
        # Sort by updated_at (most recent first)
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return sessions
    
    def get_session_metadata(self, scope_id: str) -> Optional[Dict]:
        """Get session metadata"""
        if scope_id not in self.data:
            return None
        
        return self.data[scope_id].get("metadata", {})
    
    def update_session_metadata(self, scope_id: str, metadata: Dict):
        """Update session metadata"""
        if scope_id in self.data:
            self.data[scope_id]["metadata"].update(metadata)
            self.data[scope_id]["updated_at"] = datetime.utcnow().isoformat()
            self.save()
            logger.debug(f"Updated metadata for session: {scope_id}")
    
    def clear_all(self):
        """Clear all sessions"""
        self.data = {}
        self.save()
        logger.info("Cleared all conversation sessions")
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        total_messages = sum(len(s.get("messages", [])) for s in self.data.values())
        
        # Group by scope type
        global_sessions = [s for s in self.data.keys() if s == "global"]
        asset_sessions = [s for s in self.data.keys() if s.startswith("asset:")]
        user_sessions = [s for s in self.data.keys() if s.startswith("user:")]
        
        return {
            "total_sessions": len(self.data),
            "total_messages": total_messages,
            "global_sessions": len(global_sessions),
            "asset_sessions": len(asset_sessions),
            "user_sessions": len(user_sessions),
            "database_path": str(self.db_path),
            "database_size_bytes": self.db_path.stat().st_size if self.db_path.exists() else 0
        }


# Singleton instance
_conversation_database: Optional[ConversationDatabase] = None


def get_conversation_database(db_path: str = "data/conversations.json") -> ConversationDatabase:
    """Get or create ConversationDatabase singleton"""
    global _conversation_database
    if _conversation_database is None:
        _conversation_database = ConversationDatabase(db_path)
    return _conversation_database
