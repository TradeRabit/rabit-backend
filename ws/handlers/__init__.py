"""WebSocket event handlers"""
from .market_handler import MarketDataHandler

# Global market handler instance
_market_handler = None

def get_market_handler() -> MarketDataHandler:
    """Get or create market handler singleton"""
    global _market_handler
    if _market_handler is None:
        _market_handler = MarketDataHandler()
    return _market_handler

__all__ = ["MarketDataHandler", "get_market_handler"]
