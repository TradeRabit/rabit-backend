"""Binance WebSocket client for OHLC data"""
import asyncio
import websockets
import json
from typing import Callable, Optional, List, Dict, Any
from config.settings import settings
from utils.logger import get_logger
from ws.models import OHLCData

logger = get_logger(__name__)


class BinanceClient:
    """WebSocket client for Binance OHLC data"""
    
    def __init__(self):
        """Initialize Binance WebSocket client"""
        self.url = settings.BINANCE_WS_URL
        self.interval = settings.BINANCE_OHLC_INTERVAL
        self.connected = False
        self.websocket = None
        self.callbacks: Dict[str, List[Callable]] = {}
        self.subscriptions: Dict[str, bool] = {}
    
    async def connect(self):
        """Connect to Binance WebSocket"""
        try:
            logger.info(f"Connecting to Binance WebSocket: {self.url}")
            self.websocket = await websockets.connect(self.url)
            self.connected = True
            logger.info("Connected to Binance WebSocket")
            
            # Start listening for messages
            asyncio.create_task(self._listen())
            
        except Exception as e:
            logger.error(f"Failed to connect to Binance WebSocket: {str(e)}")
            self.connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from Binance WebSocket"""
        try:
            if self.websocket:
                await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from Binance WebSocket")
        except Exception as e:
            logger.error(f"Error disconnecting: {str(e)}")
    
    async def subscribe_ohlc(self, symbol: str, callback: Callable):
        """
        Subscribe to OHLC data for a symbol
        
        Args:
            symbol: Trading symbol (e.g., SOLUSDT, BTCUSDT)
            callback: Callback function for OHLC updates
        """
        if symbol not in self.callbacks:
            self.callbacks[symbol] = []
        
        self.callbacks[symbol].append(callback)
        
        if not self.subscriptions.get(symbol, False):
            await self._send_subscription(symbol)
            self.subscriptions[symbol] = True
            logger.info(f"Subscribed to OHLC {symbol}")
    
    async def unsubscribe_ohlc(self, symbol: str):
        """
        Unsubscribe from OHLC data
        
        Args:
            symbol: Trading symbol
        """
        if symbol in self.subscriptions:
            await self._send_unsubscription(symbol)
            del self.subscriptions[symbol]
            if symbol in self.callbacks:
                del self.callbacks[symbol]
            logger.info(f"Unsubscribed from OHLC {symbol}")
    
    async def _send_subscription(self, symbol: str):
        """Send subscription message to Binance"""
        try:
            # Binance format: symbol@kline_interval
            stream = f"{symbol.lower()}@kline_{self.interval}"
            message = {
                "method": "SUBSCRIBE",
                "params": [stream],
                "id": 1
            }
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending subscription: {str(e)}")
    
    async def _send_unsubscription(self, symbol: str):
        """Send unsubscription message to Binance"""
        try:
            stream = f"{symbol.lower()}@kline_{self.interval}"
            message = {
                "method": "UNSUBSCRIBE",
                "params": [stream],
                "id": 1
            }
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending unsubscription: {str(e)}")
    
    async def _listen(self):
        """Listen for messages from Binance WebSocket"""
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
            logger.warning("Binance WebSocket connection closed")
            self.connected = False
        except Exception as e:
            logger.error(f"Error in listen loop: {str(e)}")
            self.connected = False
    
    async def _handle_message(self, data: Dict[str, Any]):
        """
        Handle incoming message from Binance
        
        Args:
            data: Message data
        """
        try:
            # Skip subscription confirmation messages
            if "result" in data:
                return
            
            if "k" in data:  # OHLC data
                kline = data["k"]
                symbol = data["s"]
                
                # Create OHLC data
                ohlc = OHLCData(
                    symbol=symbol,
                    timestamp=kline["t"],
                    open=float(kline["o"]),
                    high=float(kline["h"]),
                    low=float(kline["l"]),
                    close=float(kline["c"]),
                    volume=float(kline["v"]),
                    quote_asset_volume=float(kline.get("q", 0)),
                    number_of_trades=int(kline.get("n", 0)),
                    taker_buy_base_asset_volume=float(kline.get("V", 0)),
                    taker_buy_quote_asset_volume=float(kline.get("Q", 0))
                )
                
                # Call registered callbacks
                if symbol in self.callbacks:
                    for callback in self.callbacks[symbol]:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(ohlc)
                            else:
                                callback(ohlc)
                        except Exception as e:
                            logger.error(f"Error in callback: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
    
    def get_subscribed_symbols(self) -> List[str]:
        """Get list of subscribed symbols"""
        return list(self.subscriptions.keys())
    
    def is_subscribed(self, symbol: str) -> bool:
        """Check if symbol is subscribed"""
        return self.subscriptions.get(symbol, False)
