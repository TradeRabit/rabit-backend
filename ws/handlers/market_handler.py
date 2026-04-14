"""Market data event handlers"""
from typing import Dict, List, Callable, Optional
from utils.logger import get_logger
from ws.models import PriceUpdate, OHLCData, MarketData

logger = get_logger(__name__)


class MarketDataHandler:
    """Handle market data events from WebSocket"""
    
    def __init__(self):
        """Initialize market data handler"""
        self.price_data: Dict[str, PriceUpdate] = {}
        self.ohlc_data: Dict[str, List[OHLCData]] = {}
        self.listeners: Dict[str, List[Callable]] = {}
    
    async def on_price_update(self, price_update: PriceUpdate):
        """
        Handle price update from Drift
        
        Args:
            price_update: Price update data
        """
        try:
            symbol = price_update.symbol
            self.price_data[symbol] = price_update
            
            logger.debug(f"Price update: {symbol} = {price_update.price}")
            
            # Notify listeners
            await self._notify_listeners(f"price:{symbol}", price_update)
        
        except Exception as e:
            logger.error(f"Error handling price update: {str(e)}")
    
    async def on_ohlc_update(self, ohlc_data: OHLCData):
        """
        Handle OHLC update from Binance
        
        Args:
            ohlc_data: OHLC data
        """
        try:
            symbol = ohlc_data.symbol
            
            if symbol not in self.ohlc_data:
                self.ohlc_data[symbol] = []
            
            # Keep last 100 candles
            self.ohlc_data[symbol].append(ohlc_data)
            if len(self.ohlc_data[symbol]) > 100:
                self.ohlc_data[symbol].pop(0)
            
            logger.debug(f"OHLC update: {symbol} = {ohlc_data.close}")
            
            # Notify listeners
            await self._notify_listeners(f"ohlc:{symbol}", ohlc_data)
        
        except Exception as e:
            logger.error(f"Error handling OHLC update: {str(e)}")
    
    def subscribe(self, event: str, callback: Callable):
        """
        Subscribe to market data events
        
        Args:
            event: Event name (e.g., "price:SOL", "ohlc:SOLUSDT")
            callback: Callback function
        """
        if event not in self.listeners:
            self.listeners[event] = []
        
        self.listeners[event].append(callback)
        logger.info(f"Subscribed to event: {event}")
    
    def unsubscribe(self, event: str, callback: Callable):
        """
        Unsubscribe from market data events
        
        Args:
            event: Event name
            callback: Callback function
        """
        if event in self.listeners:
            try:
                self.listeners[event].remove(callback)
                logger.info(f"Unsubscribed from event: {event}")
            except ValueError:
                logger.warning(f"Callback not found for event: {event}")
    
    async def _notify_listeners(self, event: str, data):
        """
        Notify all listeners for an event
        
        Args:
            event: Event name
            data: Event data
        """
        if event in self.listeners:
            for callback in self.listeners[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Error in listener callback: {str(e)}")
    
    def get_price(self, symbol: str) -> Optional[PriceUpdate]:
        """
        Get latest price for a symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Latest price update or None
        """
        return self.price_data.get(symbol)
    
    def get_ohlc(self, symbol: str, limit: Optional[int] = None) -> List[OHLCData]:
        """
        Get OHLC data for a symbol
        
        Args:
            symbol: Trading symbol
            limit: Number of candles to return
            
        Returns:
            List of OHLC data
        """
        data = self.ohlc_data.get(symbol, [])
        
        if limit:
            return data[-limit:]
        
        return data
    
    def get_all_prices(self) -> Dict[str, PriceUpdate]:
        """Get all price data"""
        return self.price_data.copy()
    
    def get_all_ohlc(self) -> Dict[str, List[OHLCData]]:
        """Get all OHLC data"""
        return self.ohlc_data.copy()


# Import asyncio for async check
import asyncio
