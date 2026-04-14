"""Agent memory management with scope by ID and global"""
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel


class Message(BaseModel):
    """Message model"""
    role: str
    content: str
    timestamp: datetime = datetime.now()


class ConversationMemory:
    """Memory storage for conversations with persistent database"""
    
    def __init__(self, use_database: bool = True):
        """
        Initialize memory storage
        
        Args:
            use_database: Whether to use persistent database (default: True)
        """
        self._global_memory: List[Message] = []
        self._scoped_memory: Dict[str, List[Message]] = {}
        self.use_database = use_database
        self.db = None
        
        if use_database:
            from agents.memory.database import get_conversation_database
            self.db = get_conversation_database()
            self._load_from_database()
    
    def _load_from_database(self):
        """Load all sessions from database on initialization"""
        if not self.db:
            return
        
        # Load all sessions
        for scope_id in self.db.data.keys():
            messages = self.db.load_session(scope_id)
            if messages:
                if scope_id == "global":
                    self._global_memory = messages
                else:
                    self._scoped_memory[scope_id] = messages
    
    def _save_to_database(self, scope_id: Optional[str] = None):
        """Save session to database"""
        if not self.db:
            return
        
        if scope_id:
            # Save specific scope
            messages = self._scoped_memory.get(scope_id, [])
            if messages:
                self.db.save_session(scope_id, messages)
        else:
            # Save global
            if self._global_memory:
                self.db.save_session("global", self._global_memory)
    
    def add_message(self, message: Message, scope_id: Optional[str] = None):
        """
        Add message to memory
        
        Args:
            message: Message to add
            scope_id: Optional scope ID for scoped memory
        """
        if scope_id:
            if scope_id not in self._scoped_memory:
                self._scoped_memory[scope_id] = []
            self._scoped_memory[scope_id].append(message)
            
            # Save to database
            self._save_to_database(scope_id)
        else:
            self._global_memory.append(message)
            
            # Save to database
            self._save_to_database()
    
    def get_messages(self, scope_id: Optional[str] = None, limit: Optional[int] = None) -> List[Message]:
        """
        Get messages from memory
        
        Args:
            scope_id: Optional scope ID to get scoped messages
            limit: Optional limit for number of messages
            
        Returns:
            List of messages
        """
        if scope_id:
            messages = self._scoped_memory.get(scope_id, [])
        else:
            messages = self._global_memory
        
        if limit:
            return messages[-limit:]
        return messages
    
    def clear_scope(self, scope_id: str):
        """
        Clear scoped memory
        
        Args:
            scope_id: Scope ID to clear
        """
        if scope_id in self._scoped_memory:
            del self._scoped_memory[scope_id]
        
        # Delete from database
        if self.db:
            self.db.delete_session(scope_id)
    
    def clear_global(self):
        """Clear global memory"""
        self._global_memory = []
        
        # Delete from database
        if self.db:
            self.db.delete_session("global")
    
    def get_all_scopes(self) -> List[str]:
        """
        Get all scope IDs
        
        Returns:
            List of scope IDs
        """
        return list(self._scoped_memory.keys())
    
    def get_scope_size(self, scope_id: str) -> int:
        """
        Get size of scoped memory
        
        Args:
            scope_id: Scope ID
            
        Returns:
            Number of messages in scope
        """
        return len(self._scoped_memory.get(scope_id, []))
    
    def get_global_size(self) -> int:
        """
        Get size of global memory
        
        Returns:
            Number of messages in global memory
        """
        return len(self._global_memory)
