"""
Drift WebSocket Service
Service untuk mengelola koneksi dan data dari Drift Protocol
"""
import asyncio
from typing import Optional, List
import logging

from ws.drift.client import DriftWSClient
from ws.handlers.market_handler import MarketDataHandler
from config.settings import settings

logger = logging.getLogger(__name__)


class DriftService:
    """Service untuk mengelola Drift WebSocket connection"""

    def __init__(self):
        self.client: Optional[DriftWSClient] = None
        self.handler: Optional[MarketDataHandler] = None
        self.running = False

    async def start(self, handler: MarketDataHandler):
        """
        Start Drift WebSocket service

        Args:
            handler: MarketDataHandler instance to receive updates
        """
        if self.running:
            logger.warning("Drift service already running")
            return

        try:
            logger.info("Starting Drift WebSocket service...")

            self.handler = handler
            self.client = DriftWSClient()
            
            # Set exchange source for OHLC auto-save
            handler.set_exchange_source("drift")

            # Connect to Drift
            await self.client.connect()

            # Subscribe to all trading assets
            for symbol in settings.TRADING_ASSETS[:settings.DRIFT_SUBSCRIBE_ASSETS]:
                try:
                    # Subscribe to price updates
                    await self.client.subscribe(
                        symbol=symbol,
                        callback=handler.on_price_update,
                        subscribe_ohlc=True
                    )

                    # Subscribe to OHLC updates
                    self.client.subscribe_ohlc(
                        symbol=symbol,
                        callback=handler.on_ohlc_update
                    )

                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.1)

                except Exception as e:
                    logger.error(f"Error subscribing to {symbol}: {e}")

            self.running = True
            logger.info(f"Drift service started, subscribed to {len(settings.TRADING_ASSETS[:settings.DRIFT_SUBSCRIBE_ASSETS])} assets")

        except Exception as e:
            logger.error(f"Failed to start Drift service: {e}")
            self.running = False
            raise

    async def stop(self):
        """Stop Drift WebSocket service"""
        if not self.running:
            return

        try:
            logger.info("Stopping Drift WebSocket service...")

            if self.client:
                await self.client.disconnect()

            self.running = False
            logger.info("Drift service stopped")

        except Exception as e:
            logger.error(f"Error stopping Drift service: {e}")

    def is_running(self) -> bool:
        """Check if service is running"""
        return self.running and self.client and self.client.connected

    def get_subscribed_symbols(self) -> List[str]:
        """Get list of subscribed symbols"""
        if self.client:
            return self.client.get_subscribed_symbols()
        return []


# Singleton instance
_drift_service: Optional[DriftService] = None


def get_drift_service() -> DriftService:
    """Get or create DriftService singleton"""
    global _drift_service
    if _drift_service is None:
        _drift_service = DriftService()
    return _drift_service
