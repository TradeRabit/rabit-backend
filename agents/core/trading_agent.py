"""Trading agent example"""
from .base import BaseAgent
from typing import Optional


class TradingAgent(BaseAgent):
    """Trading assistant agent with tool support"""
    
    def __init__(self, scope_id: Optional[str] = None):
        """
        Initialize trading agent
        
        Args:
            scope_id: Optional scope ID for user-specific memory
        """
        system_prompt = """You are Rabit Agent, a helpful trading assistant for the Rabit platform.

Your name is "Rabit Agent" and you are an AI-powered trading assistant designed to help users with cryptocurrency trading on Solana.

Your capabilities:
- Get market prices for trading symbols
- Calculate position sizes based on risk management
- Provide account information
- Assist with trading decisions
- Provide market analysis and insights

When using tools:
- Always validate parameters before calling
- If a tool fails, read the error message carefully
- The error will tell you exactly what went wrong with your parameters
- Adjust your parameters based on the error details and try again

Be concise, helpful, and professional in your responses."""
        
        super().__init__(
            name="TradingAgent",
            system_prompt=system_prompt,
            scope_id=scope_id,
            max_tokens=4000
        )
    
    async def process_trading_query(self, user_input: str) -> str:
        """
        Process trading-related query with tool support
        
        Args:
            user_input: User query
            
        Returns:
            Agent response
        """
        return await self.process(user_input, use_tools=True)
