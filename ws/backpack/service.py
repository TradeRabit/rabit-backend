"""
Backpack WebSocket Service
Service untuk mengelola koneksi dan data dari Backpack Exchange
"""
import asyncio
from typing import Optional, List
import logging

from ws.backpack.client import BackpackWSClient
from ws.handlers.market_handler import MarketDataHandler
from config.settings import settings

logger = logging.getLogger(__name__)


class BackpackService:
    """Service untuk mengelola Backpack WebSocket connection"""
    
    def __init__(self):
        self.client: Optional[BackpackWSClient] = None
        self.handler: Optional[MarketDataHandler] = None
        self.running = False

    async def _on_price_update(self, price_update):
        """Forward price updates with Backpack source metadata."""
        if self.handler:
            await self.handler.on_price_update_from_exchange("backpack", price_update)

    async def _on_ohlc_update(self, ohlc_data, interval: str = "1h"):
        """Forward OHLC updates with Backpack source metadata."""
        if self.handler:
            await self.handler.on_ohlc_update_from_exchange("backpack", ohlc_data, interval)
    
    async def start(self, handler: MarketDataHandler):
        """
        Start Backpack WebSocket service
        
        Args:
            handler: MarketDataHandler instance to receive updates
        """
        if not settings.BACKPACK_ENABLED:
            logger.info("Backpack is disabled in settings")
            return
        
        if self.running:
            logger.warning("Backpack service already running")
            return
        
        try:
            logger.info("Starting Backpack WebSocket service...")
            
            self.handler = handler
            self.client = BackpackWSClient()
            
            # Connect to Backpack
            await self.client.connect()
            
            # Subscribe to all trading assets
            for symbol in settings.TRADING_ASSETS[:settings.BACKPACK_SUBSCRIBE_ASSETS]:
                try:
                    # Subscribe to price updates
                    await self.client.subscribe(
                        symbol=symbol,
                        callback=self._on_price_update,
                        subscribe_ohlc=True
                    )
                    
                    # Subscribe to OHLC updates
                    self.client.subscribe_ohlc(
                        symbol=symbol,
                        callback=self._on_ohlc_update
                    )
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error subscribing to {symbol}: {e}")
            
            self.running = True
            logger.info(f"Backpack service started, subscribed to {len(settings.TRADING_ASSETS[:settings.BACKPACK_SUBSCRIBE_ASSETS])} assets")
            
        except Exception as e:
            logger.error(f"Failed to start Backpack service: {e}")
            self.running = False
            raise
    
    async def stop(self):
        """Stop Backpack WebSocket service"""
        if not self.running:
            return
        
        try:
            logger.info("Stopping Backpack WebSocket service...")
            
            if self.client:
                await self.client.disconnect()
            
            self.running = False
            logger.info("Backpack service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Backpack service: {e}")
    
    def is_running(self) -> bool:
        """Check if service is running"""
        return self.running and self.client and self.client.connected
    
    def get_subscribed_symbols(self) -> List[str]:
        """Get list of subscribed symbols"""
        if self.client:
            return self.client.get_subscribed_symbols()
        return []


# Singleton instance
_backpack_service: Optional[BackpackService] = None


def get_backpack_service() -> BackpackService:
    """Get or create BackpackService singleton"""
    global _backpack_service
    if _backpack_service is None:
        _backpack_service = BackpackService()
    return _backpack_service
