"""Drift WebSocket client"""
import asyncio
import websockets
import json
from typing import Callable, Optional, List, Dict, Any
from config.settings import settings
from utils.logger import get_logger
from ws.models import PriceUpdate, OHLCData

logger = get_logger(__name__)


class DriftWSClient:
    """WebSocket client for Drift Protocol"""
    
    def __init__(self):
        """Initialize Drift WebSocket client"""
        self.url = settings.DRIFT_WS_URL
        self.assets = settings.TRADING_ASSETS[:settings.DRIFT_SUBSCRIBE_ASSETS]
        self.connected = False
        self.websocket = None
        self.callbacks: Dict[str, List[Callable]] = {}
        self.ohlc_callbacks: Dict[str, List[Callable]] = {}
        self.subscriptions: Dict[str, bool] = {}
        self._listen_task = None    
    async def connect(self):
        """Connect to Drift WebSocket"""
        try:
            logger.info(f"Connecting to Drift WebSocket: {self.url}")
            self.websocket = await websockets.connect(self.url)
            self.connected = True
            logger.info("Connected to Drift WebSocket")
            
            # Start listening for messages
            self._listen_task = asyncio.create_task(self._listen())
            
        except Exception as e:
            logger.error(f"Failed to connect to Drift WebSocket: {str(e)}")
            self.connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from Drift WebSocket"""
        try:
            if self._listen_task:
                self._listen_task.cancel()
                try:
                    await self._listen_task
                except asyncio.CancelledError:
                    pass

            if self.websocket:
                await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from Drift WebSocket")
        except Exception as e:
            logger.error(f"Error disconnecting: {str(e)}")
    
    async def subscribe(self, symbol: str, callback: Callable, subscribe_ohlc: bool = True):
        """
        Subscribe to market data for a symbol
        
        Args:
            symbol: Trading symbol (e.g., SOL, BTC)
            callback: Callback function for price updates
            subscribe_ohlc: Also subscribe to OHLC data (for interface parity with Backpack)
        """
        # Normalize symbol to base (e.g., "SOL-PERP" -> "SOL", "SOL_USDC" -> "SOL")
        base_symbol = symbol.split("-")[0].split("_")[0].upper()

        if base_symbol not in self.callbacks:
            self.callbacks[base_symbol] = []
        
        self.callbacks[base_symbol].append(callback)
        
        if not self.subscriptions.get(base_symbol, False):
            await self._send_subscription(base_symbol)
            self.subscriptions[base_symbol] = True
            logger.info(f"Subscribed to {base_symbol}")

    def subscribe_ohlc(self, symbol: str, callback: Callable):
        """
        Subscribe to OHLC updates for a symbol
        
        Args:
            symbol: Trading symbol (e.g., SOL, BTC)
            callback: Callback function for OHLC updates
        """
        base_symbol = symbol.split("-")[0].split("_")[0].upper()

        if base_symbol not in self.ohlc_callbacks:
            self.ohlc_callbacks[base_symbol] = []

        self.ohlc_callbacks[base_symbol].append(callback)
        logger.info(f"Registered OHLC callback for {base_symbol}")
    
    async def unsubscribe(self, symbol: str):
        """
        Unsubscribe from market data
        
        Args:
            symbol: Trading symbol
        """
        base_symbol = symbol.split("-")[0].split("_")[0].upper()
        if base_symbol in self.subscriptions:
            await self._send_unsubscription(base_symbol)
            del self.subscriptions[base_symbol]
            if base_symbol in self.callbacks:
                del self.callbacks[base_symbol]
            logger.info(f"Unsubscribed from {base_symbol}")
    
    async def _send_subscription(self, symbol: str):
        """Send subscription message to Drift"""
        try:
            message = {
                "type": "subscribe",
                "channel": "market_data",
                "symbol": symbol,
                "fields": settings.WS_DATA_FIELDS
            }
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending subscription: {str(e)}")
    
    async def _send_unsubscription(self, symbol: str):
        """Send unsubscription message to Drift"""
        try:
            message = {
                "type": "unsubscribe",
                "channel": "market_data",
                "symbol": symbol
            }
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending unsubscription: {str(e)}")
    
    async def _listen(self):
        """Listen for messages from Drift WebSocket"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"Error handling message: {str(e)}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Drift WebSocket connection closed")
            self.connected = False
        except asyncio.CancelledError:
            logger.info("Listen task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in listen loop: {str(e)}")
            self.connected = False
    
    async def _handle_message(self, data: Dict[str, Any]):
        """
        Handle incoming message from Drift
        
        Args:
            data: Message data
        """
        try:
            if data.get("type") == "market_data":
                raw_symbol = data.get("symbol", "")
                # Normalize: "SOL-PERP" -> "SOL", "SOL_USDC" -> "SOL"
                symbol = raw_symbol.split("-")[0].split("_")[0].upper()
                
                # Create price update
                price_update = PriceUpdate(
                    symbol=symbol,
                    price=data.get("price", 0),
                    change_24h=data.get("change_24h"),
                    volume_24h=data.get("volume_24h"),
                    open_interest=data.get("open_interest"),
                    funding_rate=data.get("funding_rate")
                )
                
                # Call registered callbacks
                if symbol in self.callbacks:
                    for callback in self.callbacks[symbol]:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(price_update)
                            else:
                                callback(price_update)
                        except Exception as e:
                            logger.error(f"Error in callback: {str(e)}")

            elif data.get("type") == "ohlc":
                raw_symbol = data.get("symbol", "")
                symbol = raw_symbol.split("-")[0].split("_")[0].upper()
                interval = data.get("interval", "1h")  # Get interval from message

                ohlc_data = OHLCData(
                    symbol=symbol,
                    timestamp=int(data.get("timestamp", 0)),
                    open=float(data.get("open", 0)),
                    high=float(data.get("high", 0)),
                    low=float(data.get("low", 0)),
                    close=float(data.get("close", 0)),
                    volume=float(data.get("volume", 0))
                )

                if symbol in self.ohlc_callbacks:
                    for callback in self.ohlc_callbacks[symbol]:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                # Pass interval to callback if it accepts it
                                import inspect
                                sig = inspect.signature(callback)
                                if len(sig.parameters) >= 2:
                                    await callback(ohlc_data, interval)
                                else:
                                    await callback(ohlc_data)
                            else:
                                callback(ohlc_data)
                        except Exception as e:
                            logger.error(f"Error in OHLC callback: {str(e)}")

        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
    
    def get_subscribed_symbols(self) -> List[str]:
        """Get list of subscribed symbols"""
        return list(self.subscriptions.keys())
    
    def is_subscribed(self, symbol: str) -> bool:
        """Check if symbol is subscribed"""
        return self.subscriptions.get(symbol, False)
