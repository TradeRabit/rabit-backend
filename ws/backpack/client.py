"""Backpack Exchange WebSocket client"""
import asyncio
import websockets
import json
from datetime import datetime
from typing import Callable, Optional, List, Dict, Any
from config.settings import settings
from utils.logger import get_logger
from ws.models import PriceUpdate, OHLCData

logger = get_logger(__name__)


BACKPACK_KLINE_INTERVALS = [
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
    "3d",
    "1w",
    "1month",
]


class BackpackWSClient:
    """WebSocket client for Backpack Exchange"""
    
    def __init__(self):
        """Initialize Backpack WebSocket client"""
        self.url = settings.BACKPACK_WS_URL
        self.assets = settings.TRADING_ASSETS[:settings.BACKPACK_SUBSCRIBE_ASSETS]
        self.quote_asset = settings.BACKPACK_QUOTE_ASSET
        self.connected = False
        self.websocket = None
        self.callbacks: Dict[str, List[Callable]] = {}
        self.ohlc_callbacks: Dict[str, List[Callable]] = {}
        self.subscriptions: Dict[str, bool] = {}
        self._listen_task = None
    
    async def connect(self):
        """Connect to Backpack WebSocket"""
        try:
            logger.info(f"Connecting to Backpack WebSocket: {self.url}")
            self.websocket = await websockets.connect(self.url)
            self.connected = True
            logger.info("Connected to Backpack WebSocket")
        except Exception as e:
            logger.error(f"Failed to connect to Backpack WebSocket: {str(e)}")
            self.connected = False
            raise

    def start_listening(self):
        """Start the read loop after subscriptions are registered."""
        if self._listen_task is None:
            self._listen_task = asyncio.create_task(self._listen())
    
    async def disconnect(self):
        """Disconnect from Backpack WebSocket"""
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
            logger.info("Disconnected from Backpack WebSocket")
        except Exception as e:
            logger.error(f"Error disconnecting: {str(e)}")
    
    async def subscribe(self, symbol: str, callback: Callable, subscribe_ohlc: bool = True):
        """
        Subscribe to market data for a symbol
        
        Args:
            symbol: Trading symbol (e.g., SOL, BTC)
            callback: Callback function for price updates
            subscribe_ohlc: Also subscribe to kline data for OHLC
        """
        # Normalize symbol to base (e.g., "SOL_USDC" -> "SOL")
        base_symbol = symbol.split("_")[0] if "_" in symbol else symbol
        base_symbol = base_symbol.upper()
        
        # Create Backpack symbol format (e.g., "SOL_USDC")
        backpack_symbol = f"{base_symbol}_{self.quote_asset}"
        
        if backpack_symbol not in self.callbacks:
            self.callbacks[backpack_symbol] = []
        
        self.callbacks[backpack_symbol].append(callback)
        
        if not self.subscriptions.get(backpack_symbol, False):
            await self._send_subscription(backpack_symbol, subscribe_ohlc)
            self.subscriptions[backpack_symbol] = True
            logger.info(f"Subscribed to {backpack_symbol}")
    
    def subscribe_ohlc(self, symbol: str, callback: Callable):
        """
        Subscribe to OHLC updates for a symbol
        
        Args:
            symbol: Trading symbol (e.g., SOL, BTC)
            callback: Callback function for OHLC updates
        """
        base_symbol = symbol.split("_")[0] if "_" in symbol else symbol
        base_symbol = base_symbol.upper()
        backpack_symbol = f"{base_symbol}_{self.quote_asset}"
        
        if backpack_symbol not in self.ohlc_callbacks:
            self.ohlc_callbacks[backpack_symbol] = []
        
        self.ohlc_callbacks[backpack_symbol].append(callback)
        logger.info(f"Registered OHLC callback for {backpack_symbol}")
    
    async def unsubscribe(self, symbol: str):
        """
        Unsubscribe from market data
        
        Args:
            symbol: Trading symbol
        """
        if symbol in self.subscriptions:
            await self._send_unsubscription(symbol)
            del self.subscriptions[symbol]
            if symbol in self.callbacks:
                del self.callbacks[symbol]
            logger.info(f"Unsubscribed from {symbol}")
    
    async def _send_subscription(self, symbol: str, subscribe_ohlc: bool = True):
        """
        Send subscription message to Backpack
        Subscribe to ticker, trade, and kline streams for comprehensive market data
        
        Args:
            symbol: Backpack symbol format (e.g., SOL_USDC)
            subscribe_ohlc: Also subscribe to kline data
        """
        try:
            # Backpack uses format: <stream_type>.<symbol>
            # Subscribe to multiple streams for comprehensive data
            streams = [
                f"ticker.{symbol}",  # 24h ticker data
                f"trade.{symbol}",   # Recent trades
            ]
            
            # Add kline stream for OHLC data
            if subscribe_ohlc:
                streams.extend(
                    f"kline.{interval}.{symbol}"
                    for interval in BACKPACK_KLINE_INTERVALS
                )
            
            message = {
                "method": "SUBSCRIBE",
                "params": streams
            }
            
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Sent subscription for {symbol}: {streams}")
            
        except Exception as e:
            logger.error(f"Error sending subscription: {str(e)}")
    
    async def _send_unsubscription(self, symbol: str):
        """Send unsubscription message to Backpack"""
        try:
            streams = [
                f"ticker.{symbol}",
                f"trade.{symbol}",
            ]
            streams.extend(
                f"kline.{interval}.{symbol}"
                for interval in BACKPACK_KLINE_INTERVALS
            )
            
            message = {
                "method": "UNSUBSCRIBE",
                "params": streams
            }
            
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Sent unsubscription for {symbol}")
            
        except Exception as e:
            logger.error(f"Error sending unsubscription: {str(e)}")
    
    async def _listen(self):
        """Listen for messages from Backpack WebSocket"""
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
            logger.warning("Backpack WebSocket connection closed")
            self.connected = False
        except asyncio.CancelledError:
            logger.info("Listen task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in listen loop: {str(e)}")
            self.connected = False
    
    async def _handle_message(self, data: Dict[str, Any]):
        """
        Handle incoming message from Backpack
        
        Backpack WebSocket message format:
        {
            "stream": "ticker.SOL_USDC",
            "data": {
                "symbol": "SOL_USDC",
                "lastPrice": "150.50",
                "high": "155.00",
                "low": "148.00",
                "volume": "1000000",
                "priceChange": "2.50",
                "priceChangePercent": "1.69",
                ...
            }
        }
        
        Kline format:
        {
            "stream": "kline.SOL_USDC.1h",
            "data": {
                "symbol": "SOL_USDC",
                "interval": "1h",
                "startTime": 1234567890000,
                "endTime": 1234567890000,
                "open": "150.00",
                "high": "155.00",
                "low": "148.00",
                "close": "152.00",
                "volume": "10000",
                ...
            }
        }
        """
        try:
            # Check if this is a subscription confirmation
            if data.get("result") is not None:
                logger.debug(f"Subscription confirmation: {data}")
                return

            # Legacy wrapper format
            if "stream" in data and "data" in data:
                stream = data.get("stream", "")
                stream_data = data.get("data", {})
                parts = stream.split(".")

                if len(parts) < 2:
                    return

                stream_type = parts[0]

                if stream_type == "kline":
                    interval = parts[1] if len(parts) > 2 else "1h"
                    symbol = parts[2] if len(parts) > 2 else parts[1]
                    await self._handle_kline(symbol, interval, stream_data)
                elif stream_type == "ticker":
                    await self._handle_ticker(parts[1], stream_data)
                elif stream_type == "trade":
                    await self._handle_trade(parts[1], stream_data)

                return

            # Current flattened format
            stream_type = data.get("e")
            symbol = data.get("s")

            if not stream_type or not symbol:
                return

            if stream_type == "ticker":
                await self._handle_ticker(symbol, data)
            elif stream_type == "trade":
                await self._handle_trade(symbol, data)
            elif stream_type == "kline":
                interval = self._extract_kline_interval(data)
                await self._handle_kline(symbol, interval, data)
        
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    @staticmethod
    def _extract_kline_interval(data: Dict[str, Any]) -> str:
        """Extract kline interval from flattened or legacy payload."""
        interval = data.get("interval") or data.get("i")
        if interval:
            return interval

        return "1h"

    @staticmethod
    def _parse_float_value(raw_value: Any) -> Optional[float]:
        """Parse numeric websocket values without crashing on partial payloads."""
        if raw_value is None:
            return None

        if isinstance(raw_value, (int, float)):
            return float(raw_value)

        if isinstance(raw_value, str):
            value = raw_value.strip()
            if not value:
                return None
            return float(value)

        return None

    @classmethod
    def _parse_float_field(cls, data: Dict[str, Any], *keys: str, default: Optional[float] = None) -> Optional[float]:
        for key in keys:
            if key in data:
                parsed = cls._parse_float_value(data.get(key))
                if parsed is not None:
                    return parsed
        return default

    @staticmethod
    def _parse_timestamp_ms(raw_value: Any) -> int:
        """Normalize Backpack timestamps into milliseconds."""
        if raw_value is None:
            return 0

        if isinstance(raw_value, (int, float)):
            value = int(raw_value)
            # Backpack docs use microseconds for websocket timestamps.
            return value // 1000 if value > 10**12 else value

        if isinstance(raw_value, str):
            value = raw_value.strip()
            if not value:
                return 0

            if value.isdigit():
                parsed = int(value)
                return parsed // 1000 if parsed > 10**12 else parsed

            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return int(dt.timestamp() * 1000)
            except ValueError:
                return 0

        return 0
    
    async def _handle_ticker(self, symbol: str, data: Dict[str, Any]):
        """
        Handle ticker data from Backpack
        
        Ticker data includes 24h statistics:
        - lastPrice: Current price
        - priceChange: 24h price change
        - priceChangePercent: 24h price change percentage
        - volume: 24h volume
        - high: 24h high
        - low: 24h low
        """
        try:
            # Extract base symbol (e.g., "SOL_USDC" -> "SOL")
            base_symbol = symbol.split("_")[0] if "_" in symbol else symbol
            
            # Parse ticker data
            last_price = self._parse_float_field(data, "lastPrice", "c", default=0.0) or 0.0
            high_24h = self._parse_float_field(data, "high", "h", default=0.0) or 0.0
            low_24h = self._parse_float_field(data, "low", "l", default=0.0) or 0.0
            volume = self._parse_float_field(data, "quoteVolume", "V", "volume", "v", default=0.0) or 0.0

            price_change_percent = data.get("priceChangePercent")
            if price_change_percent is None:
                open_price = self._parse_float_field(data, "open", "o", default=0.0) or 0.0
                price_change_percent = ((last_price - open_price) / open_price * 100) if open_price else None
            else:
                price_change_percent = self._parse_float_value(price_change_percent)
            
            # Create price update
            price_update = PriceUpdate(
                symbol=base_symbol,
                price=last_price,
                change_24h=price_change_percent,
                volume_24h=volume,
                high_24h=high_24h,
                low_24h=low_24h,
                open_interest=None,  # Backpack doesn't provide OI in ticker
                funding_rate=None    # Backpack doesn't provide funding in ticker
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
        
        except Exception as e:
            logger.error(f"Error handling ticker: {str(e)}")
    
    async def _handle_trade(self, symbol: str, data: Dict[str, Any]):
        """
        Handle trade data from Backpack
        
        Trade data includes:
        - price: Trade price
        - quantity: Trade quantity
        - timestamp: Trade timestamp
        - side: Buy or Sell
        """
        try:
            # We can use trade data to update price in real-time
            # This provides more frequent updates than ticker
            base_symbol = symbol.split("_")[0] if "_" in symbol else symbol
            
            # Parse trade data
            price = self._parse_float_field(data, "price", "p")
            if price is None:
                return
            
            # Create minimal price update from trade
            price_update = PriceUpdate(
                symbol=base_symbol,
                price=price,
                change_24h=None,
                volume_24h=None,
                open_interest=None,
                funding_rate=None
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
        
        except Exception as e:
            logger.error(f"Error handling trade: {str(e)}")
    
    async def _handle_kline(self, symbol: str, interval: str, data: Dict[str, Any]):
        """
        Handle kline (candlestick) data from Backpack
        
        Kline data includes:
        - startTime: Candle start timestamp
        - endTime: Candle end timestamp
        - open: Opening price
        - high: Highest price
        - low: Lowest price
        - close: Closing price
        - volume: Trading volume
        """
        try:
            base_symbol = symbol.split("_")[0] if "_" in symbol else symbol
            
            # Parse kline data
            timestamp = self._parse_timestamp_ms(data.get("startTime", data.get("t")))
            open_price = self._parse_float_field(data, "open", "o")
            high_price = self._parse_float_field(data, "high", "h")
            low_price = self._parse_float_field(data, "low", "l")
            close_price = self._parse_float_field(data, "close", "c")
            volume = self._parse_float_field(data, "volume", "v", default=0.0) or 0.0

            if None in (open_price, high_price, low_price, close_price):
                logger.debug(
                    "Skipping incomplete kline payload for %s (%s): %s",
                    symbol,
                    interval,
                    data,
                )
                return
            
            # Create OHLC data
            ohlc_data = OHLCData(
                symbol=base_symbol,
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume
            )
            
            # Call registered OHLC callbacks
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
            logger.error(f"Error handling kline: {str(e)}")
    
    def get_subscribed_symbols(self) -> List[str]:
        """Get list of subscribed symbols"""
        return list(self.subscriptions.keys())
    
    def is_subscribed(self, symbol: str) -> bool:
        """Check if symbol is subscribed"""
        return self.subscriptions.get(symbol, False)
