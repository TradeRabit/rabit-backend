"""Auto conversation compression utilities"""
import tiktoken
from typing import Any, Dict, List
from anthropic import Anthropic
from config.settings import settings


class ConversationCompressor:
    """Compress conversation history automatically"""
    
    def __init__(self, max_tokens: int = 4000, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize compressor
        
        Args:
            max_tokens: Maximum tokens before compression
            model: Model name for token counting
        """
        self.max_tokens = max_tokens
        self.model = model
        
        # Configure client based on USE_OPENROUTER setting
        if settings.USE_OPENROUTER:
            self.client = Anthropic(
                api_key=settings.OPENROUTER_API_KEY,
                base_url=settings.OPENROUTER_BASE_URL
            )
        else:
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        try:
            self.encoding = tiktoken.encoding_for_model("gpt-4")
        except:
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Count tokens in messages
        
        Args:
            messages: List of messages
            
        Returns:
            Token count
        """
        total_tokens = 0
        for message in messages:
            content = self._stringify_content(message.get("content", ""))
            total_tokens += len(self.encoding.encode(content))
        return total_tokens

    def needs_compression(self, messages: List[Dict[str, Any]]) -> bool:
        """
        Check if conversation needs compression
        
        Args:
            messages: List of messages
            
        Returns:
            True if compression needed
        """
        return self.count_tokens(messages) > self.max_tokens
    
    async def compress(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compress conversation history
        
        Args:
            messages: List of messages to compress
            
        Returns:
            Compressed messages
        """
        if not self.needs_compression(messages):
            return messages
        
        # Keep first message (system) and last few messages
        if len(messages) <= 3:
            return messages
        
        # Compress middle messages
        system_message = messages[0] if messages[0]["role"] == "system" else None
        recent_messages = messages[-2:]  # Keep last 2 messages
        middle_messages = messages[1:-2] if system_message else messages[:-2]
        
        # Create summary of middle messages
        summary_prompt = self._create_summary_prompt(middle_messages)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": summary_prompt}]
            )
            
            summary = response.content[0].text
            
            # Build compressed conversation
            compressed = []
            if system_message:
                compressed.append(system_message)
            
            compressed.append({
                "role": "user",
                "content": f"[Previous conversation summary]: {summary}"
            })
            
            compressed.extend(recent_messages)
            
            return compressed
            
        except Exception as e:
            # If compression fails, return original with truncation
            return self._truncate_messages(messages)
    
    def _create_summary_prompt(self, messages: List[Dict[str, Any]]) -> str:
        """
        Create prompt for summarization
        
        Args:
            messages: Messages to summarize
            
        Returns:
            Summary prompt
        """
        conversation = "\n".join([
            f"{msg['role']}: {self._stringify_content(msg.get('content', ''))}"
            for msg in messages
        ])
        
        return f"""Summarize the following conversation concisely, keeping key information and context:

{conversation}

Provide a brief summary (max 200 words) that captures the main points and context."""
    
    def _truncate_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Truncate messages if compression fails
        
        Args:
            messages: Messages to truncate
            
        Returns:
            Truncated messages
        """
        # Keep system message and last 3 messages
        if len(messages) <= 4:
            return messages
        
        system_message = messages[0] if messages[0]["role"] == "system" else None
        result = []
        
        if system_message:
            result.append(system_message)
        
        result.extend(messages[-3:])
        return result

    def _stringify_content(self, content: Any) -> str:
        """Convert multimodal message content into plain text for compression."""
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, dict):
                    block_type = block.get("type")
                    if block_type == "text":
                        parts.append(str(block.get("text", "")))
                    elif block_type in {"image", "document", "image_url", "file"}:
                        parts.append(f"[{block_type}]")
                    elif block_type == "tool_result":
                        parts.append(str(block.get("content", "")))
                    else:
                        parts.append(str(block))
                else:
                    parts.append(str(block))
            return "\n".join(part for part in parts if part)

        return str(content)
