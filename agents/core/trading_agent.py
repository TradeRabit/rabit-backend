"""Trading agent example"""
from .base import BaseAgent
from typing import Any, Dict, List, Optional

from agents.pipeline.conversation_style import CONVERSATION_STYLE_NORMAL
from agents.pipeline.trading_style import TRADING_STYLE_BALANCED
from agents.system_prompts import get_trading_agent_prompt
from agents.uploads import AgentAttachment


class TradingAgent(BaseAgent):
    """Trading assistant agent with tool support"""
    
    def __init__(self, scope_id: Optional[str] = None, user_id: Optional[str] = None):
        """
        Initialize trading agent
        
        Args:
            scope_id: Optional scope ID for user-specific memory
            user_id: Optional user ID for long-term Mem0 memory
        """
        super().__init__(
            name="TradingAgent",
            system_prompt=get_trading_agent_prompt(),
            scope_id=scope_id,
            user_id=user_id,
            max_tokens=4000
        )
    
    async def process_trading_query(
        self,
        user_input: str,
        attachments: Optional[List[AgentAttachment]] = None,
        conversation_style: str = CONVERSATION_STYLE_NORMAL,
        trading_style: str = TRADING_STYLE_BALANCED,
        market_context: Optional[Dict[str, Any]] = None,
        backpack_execution: Optional[Dict[str, Any]] = None,
        drift_execution: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Process trading-related query with tool support
        
        Args:
            user_input: User query
            attachments: Optional multimodal attachments
            conversation_style: Requested frontend response style
            trading_style: Requested frontend trading-analysis style
            market_context: Frontend market scope and market-state context
            backpack_execution: Frontend Backpack live execution gate
            drift_execution: Frontend Drift live execution gate
            
        Returns:
            Agent response
        """
        return await self.process(
            user_input,
            use_tools=True,
            attachments=attachments,
            conversation_style=conversation_style,
            trading_style=trading_style,
            market_context=market_context,
            backpack_execution=backpack_execution,
            drift_execution=drift_execution,
        )
