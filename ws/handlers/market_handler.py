"""Market data event handlers"""
from typing import Dict, List, Callable, Optional
import asyncio
from utils.logger import get_logger
from ws.models import PriceUpdate, OHLCData, MarketData
from ws.database import get_ohlc_database

logger = get_logger(__name__)


class MarketDataHandler:
    """Handle market data events from WebSocket"""
    
    def __init__(self, auto_save_ohlc: bool = True):
        """
        Initialize market data handler
        
        Args:
            auto_save_ohlc: Automatically save OHLC data to database
        """
        self.price_data: Dict[str, PriceUpdate] = {}
        self.ohlc_data: Dict[str, Dict[str, List[OHLCData]]] = {}  # symbol -> interval -> candles
        self.listeners: Dict[str, List[Callable]] = {}
        self.auto_save_ohlc = auto_save_ohlc
        self.db = get_ohlc_database() if auto_save_ohlc else None
        self.exchange_source: Optional[str] = None  # Track which exchange is sending data
    
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
            await self._notify_listeners("price:*", price_update)
        
        except Exception as e:
            logger.error(f"Error handling price update: {str(e)}")

    async def on_price_update_from_exchange(self, exchange: str, price_update: PriceUpdate):
        """
        Handle price update with explicit exchange source.

        Args:
            exchange: Exchange name ('drift', 'backpack', etc.)
            price_update: Price update data
        """
        self.exchange_source = exchange.lower()
        await self.on_price_update(price_update)
    
    async def on_ohlc_update(self, ohlc_data: OHLCData, interval: str = "1h"):
        """
        Handle OHLC update from Backpack, Binance, or Drift
        
        Args:
            ohlc_data: OHLC data
            interval: Candle interval (e.g., '1m', '5m', '1h', '1d')
        """
        try:
            symbol = ohlc_data.symbol
            
            # Store by interval
            if symbol not in self.ohlc_data:
                self.ohlc_data[symbol] = {}
            
            if interval not in self.ohlc_data[symbol]:
                self.ohlc_data[symbol][interval] = []
            
            # Keep last 1000 candles per interval
            self.ohlc_data[symbol][interval].append(ohlc_data)
            if len(self.ohlc_data[symbol][interval]) > 1000:
                self.ohlc_data[symbol][interval].pop(0)
            
            logger.debug(f"OHLC update: {symbol} ({interval}) = {ohlc_data.close}")
            
            # Auto-save to database
            if self.auto_save_ohlc and self.db and self.exchange_source:
                self.db.save_candles(
                    symbol=symbol,
                    exchange=self.exchange_source,
                    interval=interval,
                    candles=[ohlc_data],
                    merge=True
                )
            
            # Notify listeners
            await self._notify_listeners(f"ohlc:{symbol}:{interval}", ohlc_data)
            await self._notify_listeners(f"ohlc:{symbol}", ohlc_data)  # Also notify generic
            await self._notify_listeners("ohlc:*", ohlc_data)
        
        except Exception as e:
            logger.error(f"Error handling OHLC update: {str(e)}")

    async def on_ohlc_update_from_exchange(
        self,
        exchange: str,
        ohlc_data: OHLCData,
        interval: str = "1h"
    ):
        """
        Handle OHLC update with explicit exchange source.

        Args:
            exchange: Exchange name ('drift', 'backpack', etc.)
            ohlc_data: OHLC data
            interval: Candle interval
        """
        try:
            symbol = ohlc_data.symbol

            if symbol not in self.ohlc_data:
                self.ohlc_data[symbol] = {}

            if interval not in self.ohlc_data[symbol]:
                self.ohlc_data[symbol][interval] = []

            self.ohlc_data[symbol][interval].append(ohlc_data)
            if len(self.ohlc_data[symbol][interval]) > 1000:
                self.ohlc_data[symbol][interval].pop(0)

            logger.debug(f"OHLC update: {symbol} ({interval}) from {exchange} = {ohlc_data.close}")

            if self.auto_save_ohlc and self.db:
                self.db.save_candles(
                    symbol=symbol,
                    exchange=exchange.lower(),
                    interval=interval,
                    candles=[ohlc_data],
                    merge=True
                )

            await self._notify_listeners(f"ohlc:{symbol}:{interval}", ohlc_data)
            await self._notify_listeners(f"ohlc:{symbol}", ohlc_data)
            await self._notify_listeners("ohlc:*", ohlc_data)
        except Exception as e:
            logger.error(f"Error handling OHLC update from exchange: {str(e)}")
    
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
    
    def get_ohlc(self, symbol: str, interval: Optional[str] = None, limit: Optional[int] = None) -> List[OHLCData]:
        """
        Get OHLC data for a symbol
        
        Args:
            symbol: Trading symbol
            interval: Specific interval (e.g., "1h", "1d") or None for realtime
            limit: Number of candles to return
            
        Returns:
            List of OHLC data
        """
        if symbol not in self.ohlc_data:
            return []
        
        # If interval specified, get that specific interval
        if interval and interval in self.ohlc_data[symbol]:
            data = self.ohlc_data[symbol][interval]
        # Otherwise get realtime data
        elif "realtime" in self.ohlc_data[symbol]:
            data = self.ohlc_data[symbol]["realtime"]
        else:
            return []
        
        if limit:
            return data[-limit:]
        
        return data
    
    def get_all_prices(self) -> Dict[str, PriceUpdate]:
        """Get all price data"""
        return self.price_data.copy()
    
    def get_all_ohlc(self) -> Dict[str, Dict[str, List[OHLCData]]]:
        """Get all OHLC data"""
        return self.ohlc_data.copy()
    
    def set_exchange_source(self, exchange: str):
        """
        Set the exchange source for auto-saving OHLC data
        
        Args:
            exchange: Exchange name ('binance', 'backpack', 'drift')
        """
        self.exchange_source = exchange.lower()
        logger.info(f"Set exchange source for OHLC auto-save: {self.exchange_source}")


# Import asyncio for async check
import asyncio
