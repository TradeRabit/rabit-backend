"""Base agent class for Claude Agent SDK"""
from typing import Optional, List, Dict, Any
from anthropic import Anthropic
from config.settings import settings
from agents.memory import ConversationMemory, Message
from agents.compression import ConversationCompressor
from agents.tools import tool_registry, ToolResult
from utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)


class BaseAgent:
    """Base agent class using Claude Agent SDK with memory and compression"""
    
    def __init__(
        self, 
        name: str, 
        system_prompt: str = "",
        scope_id: Optional[str] = None,
        max_tokens: int = 4000,
        model: str = "claude-3-5-sonnet-20241022"
    ):
        """
        Initialize base agent
        
        Args:
            name: Agent name
            system_prompt: System prompt for the agent
            scope_id: Optional scope ID for memory isolation
            max_tokens: Max tokens before auto-compression
            model: Claude model to use (ignored if USE_OPENROUTER=true)
        """
        self.name = name
        self.system_prompt = system_prompt
        self.scope_id = scope_id
        
        # Configure client based on USE_OPENROUTER setting
        if settings.USE_OPENROUTER:
            # Use OpenRouter
            self.model = settings.OPENROUTER_MODEL
            self.client = Anthropic(
                api_key=settings.OPENROUTER_API_KEY,
                base_url=settings.OPENROUTER_BASE_URL
            )
            logger.info(f"Initialized agent with OpenRouter: {name} (model: {self.model})")
        else:
            # Use Anthropic directly
            self.model = model
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            logger.info(f"Initialized agent with Anthropic: {name} (model: {self.model})")
        
        # Initialize components
        self.memory = ConversationMemory()
        self.compressor = ConversationCompressor(max_tokens=max_tokens, model=self.model)
        
        logger.info(f"Agent scope: {scope_id or 'global'}")
    
    def add_message(self, role: str, content: str):
        """
        Add message to conversation history with memory
        
        Args:
            role: Message role (user/assistant)
            content: Message content
        """
        message = Message(role=role, content=content, timestamp=datetime.now())
        self.memory.add_message(message, self.scope_id)
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get conversation history
        
        Args:
            limit: Optional limit for messages
            
        Returns:
            List of messages as dicts
        """
        messages = self.memory.get_messages(self.scope_id, limit)
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    def clear_history(self):
        """Clear conversation history"""
        if self.scope_id:
            self.memory.clear_scope(self.scope_id)
        else:
            self.memory.clear_global()
        logger.info(f"Cleared history for agent: {self.name}")
    
    async def process(self, user_input: str, use_tools: bool = False) -> str:
        """
        Process user input with auto-compression and tool support
        
        Args:
            user_input: User input message
            use_tools: Whether to enable tool calling
            
        Returns:
            Agent response
        """
        # Add user message
        self.add_message("user", user_input)
        
        # Get conversation history
        history = self.get_conversation_history()
        
        # Auto-compress if needed
        if self.compressor.needs_compression(history):
            logger.info(f"Auto-compressing conversation for agent: {self.name}")
            history = await self.compressor.compress(history)
        
        # Prepare messages
        messages = history
        
        try:
            # Call Claude API
            if use_tools:
                response = await self._process_with_tools(messages)
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=self.system_prompt,
                    messages=messages
                )
                response_text = response.content[0].text
            
            # Add assistant response
            self.add_message("assistant", response_text if not use_tools else response)
            
            return response_text if not use_tools else response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            error_msg = f"Error: {str(e)}"
            self.add_message("assistant", error_msg)
            return error_msg
    
    async def _process_with_tools(self, messages: List[Dict[str, str]]) -> str:
        """
        Process with tool calling support
        
        Args:
            messages: Conversation messages
            
        Returns:
            Final response text
        """
        tools_schema = tool_registry.get_tools_schema()
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=self.system_prompt,
            messages=messages,
            tools=tools_schema
        )
        
        # Handle tool calls
        if response.stop_reason == "tool_use":
            tool_results = []
            
            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input
                    
                    logger.info(f"Executing tool: {tool_name}")
                    
                    # Execute tool
                    result = await tool_registry.execute(tool_name, tool_input)
                    
                    if not result.success:
                        # Format detailed error for agent
                        error_message = self._format_tool_error(result)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": error_message
                        })
                    else:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": str(result.data)
                        })
            
            # Continue conversation with tool results
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            
            # Get final response
            final_response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=self.system_prompt,
                messages=messages,
                tools=tools_schema
            )
            
            return final_response.content[0].text
        
        return response.content[0].text
    
    def _format_tool_error(self, result: ToolResult) -> str:
        """
        Format tool error with detailed explanation
        
        Args:
            result: Tool result with error
            
        Returns:
            Formatted error message
        """
        error_msg = f"Tool execution failed: {result.error}\n\n"
        
        if result.error_details:
            error_msg += "Details:\n"
            
            if "validation_errors" in result.error_details:
                error_msg += "\nParameter Validation Errors:\n"
                for err in result.error_details["validation_errors"]:
                    error_msg += f"  - {err['parameter']}: {err['error']}\n"
                    if "description" in err:
                        error_msg += f"    Expected: {err['description']}\n"
            
            if "expected_parameters" in result.error_details:
                error_msg += "\nExpected Parameters:\n"
                for param in result.error_details["expected_parameters"]:
                    required = "required" if param["required"] else "optional"
                    error_msg += f"  - {param['name']} ({param['type']}, {required}): {param['description']}\n"
            
            if "provided_parameters" in result.error_details:
                error_msg += f"\nYou provided: {', '.join(result.error_details['provided_parameters'])}\n"
            
            if "suggestion" in result.error_details:
                error_msg += f"\nSuggestion: {result.error_details['suggestion']}\n"
        
        return error_msg
