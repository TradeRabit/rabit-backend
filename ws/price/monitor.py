"""
Price WebSocket Monitor
Real-time price monitoring with validation/invalidation alerts
"""

import asyncio
import logging
from typing import Set, Dict, Optional, List, Callable
from datetime import datetime
from ws.handlers.market_handler import MarketDataHandler

logger = logging.getLogger(__name__)


class PriceAlert:
    """Price alert configuration"""
    
    def __init__(
        self,
        alert_id: str,
        symbol: str,
        validation_price: float,
        invalidation_price: float,
        direction: str = "LONG",  # LONG or SHORT
        exchange: str = "drift",  # drift, backpack, or binance
        created_at: Optional[datetime] = None
    ):
        self.alert_id = alert_id
        self.symbol = symbol.upper()
        self.validation_price = validation_price
        self.invalidation_price = invalidation_price
        self.direction = direction.upper()
        self.exchange = exchange.lower()
        self.created_at = created_at or datetime.now()
        self.triggered = False
        self.trigger_type = None  # "VALIDATION" or "INVALIDATION"
        self.trigger_price = None
        self.trigger_time = None
    
    def check_price(self, current_price: float) -> Optional[str]:
        """
        Check if price triggers validation or invalidation
        
        Returns:
            "VALIDATION" or "INVALIDATION" if triggered, None otherwise
        """
        if self.triggered:
            return None
        
        if self.direction == "LONG":
            # For LONG: validation = price goes UP, invalidation = price goes DOWN
            if current_price >= self.validation_price:
                self.triggered = True
                self.trigger_type = "VALIDATION"
                self.trigger_price = current_price
                self.trigger_time = datetime.now()
                return "VALIDATION"
            elif current_price <= self.invalidation_price:
                self.triggered = True
                self.trigger_type = "INVALIDATION"
                self.trigger_price = current_price
                self.trigger_time = datetime.now()
                return "INVALIDATION"
        
        elif self.direction == "SHORT":
            # For SHORT: validation = price goes DOWN, invalidation = price goes UP
            if current_price <= self.validation_price:
                self.triggered = True
                self.trigger_type = "VALIDATION"
                self.trigger_price = current_price
                self.trigger_time = datetime.now()
                return "VALIDATION"
            elif current_price >= self.invalidation_price:
                self.triggered = True
                self.trigger_type = "INVALIDATION"
                self.trigger_price = current_price
                self.trigger_time = datetime.now()
                return "INVALIDATION"
        
        return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "alert_id": self.alert_id,
            "symbol": self.symbol,
            "validation_price": self.validation_price,
            "invalidation_price": self.invalidation_price,
            "direction": self.direction,
            "exchange": self.exchange,
            "created_at": self.created_at.isoformat(),
            "triggered": self.triggered,
            "trigger_type": self.trigger_type,
            "trigger_price": self.trigger_price,
            "trigger_time": self.trigger_time.isoformat() if self.trigger_time else None
        }


class PriceMonitor:
    """
    Real-time price monitor with validation/invalidation alerts
    Polls for price updates and broadcasts alerts when triggered
    """
    
    def __init__(
        self,
        poll_interval: int = 10,  # 10 seconds
        alert_callback: Optional[Callable] = None,
        market_handler: Optional[MarketDataHandler] = None
    ):
        """
        Initialize price monitor
        
        Args:
            poll_interval: Polling interval in seconds (default: 10)
            alert_callback: Callback function for alerts (agent.chat)
            market_handler: MarketDataHandler instance (uses singleton if not provided)
        """
        self.poll_interval = poll_interval
        self.alert_callback = alert_callback
        
        self.running = False
        self.alerts: Dict[str, PriceAlert] = {}  # alert_id -> PriceAlert
        self.subscribers: Set[asyncio.Queue] = set()
        
        # Use provided market handler or get singleton
        if market_handler:
            self.market_handler = market_handler
        else:
            from ws.handlers import get_market_handler
            self.market_handler = get_market_handler()
        
        # Cache for price data
        self.price_cache: Dict[str, Dict] = {}  # symbol -> {price, timestamp}
        
        # Statistics
        self.stats = {
            "total_alerts": 0,
            "active_alerts": 0,
            "triggered_alerts": 0,
            "validations": 0,
            "invalidations": 0,
            "price_checks": 0
        }
        
        logger.info(f"Price monitor initialized (poll: {poll_interval}s)")
    
    async def start(self):
        """Start monitoring prices"""
        if self.running:
            logger.warning("Price monitor already running")
            return
        
        self.running = True
        logger.info("Price monitor started")
        
        # Start monitoring loop
        asyncio.create_task(self._monitor_loop())
    
    async def stop(self):
        """Stop monitoring prices"""
        self.running = False
        logger.info("Price monitor stopped")
    
    def subscribe(self) -> asyncio.Queue:
        """
        Subscribe to price alerts
        
        Returns:
            Queue that receives price alerts
        """
        queue = asyncio.Queue()
        self.subscribers.add(queue)
        logger.info(f"New subscriber added (total: {len(self.subscribers)})")
        return queue
    
    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from price alerts"""
        if queue in self.subscribers:
            self.subscribers.remove(queue)
            logger.info(f"Subscriber removed (total: {len(self.subscribers)})")
    
    def add_alert(
        self,
        symbol: str,
        validation_price: float,
        invalidation_price: float,
        direction: str = "LONG",
        exchange: str = "drift",
        alert_id: Optional[str] = None
    ) -> str:
        """
        Add price alert
        
        Args:
            symbol: Trading symbol (e.g., BTC, ETH)
            validation_price: Price level for validation
            invalidation_price: Price level for invalidation
            direction: Trade direction (LONG or SHORT)
            exchange: Exchange to monitor (drift, backpack, binance)
            alert_id: Optional custom alert ID
            
        Returns:
            Alert ID
        """
        # Generate alert ID if not provided
        if not alert_id:
            alert_id = f"{symbol}_{direction}_{exchange}_{datetime.now().timestamp()}"
        
        # Validate direction
        if direction.upper() not in ["LONG", "SHORT"]:
            raise ValueError("Direction must be LONG or SHORT")
        
        # Validate exchange
        if exchange.lower() not in ["drift", "backpack", "binance"]:
            raise ValueError("Exchange must be drift, backpack, or binance")
        
        # Validate prices
        if direction.upper() == "LONG":
            if validation_price <= invalidation_price:
                raise ValueError("For LONG: validation_price must be > invalidation_price")
        else:  # SHORT
            if validation_price >= invalidation_price:
                raise ValueError("For SHORT: validation_price must be < invalidation_price")
        
        # Create alert
        alert = PriceAlert(
            alert_id=alert_id,
            symbol=symbol,
            validation_price=validation_price,
            invalidation_price=invalidation_price,
            direction=direction,
            exchange=exchange
        )
        
        self.alerts[alert_id] = alert
        self.stats["total_alerts"] += 1
        self.stats["active_alerts"] = len([a for a in self.alerts.values() if not a.triggered])
        
        logger.info(f"Added alert: {symbol} {direction} on {exchange} | Val: {validation_price} | Inval: {invalidation_price}")
        
        return alert_id
    
    def remove_alert(self, alert_id: str) -> bool:
        """
        Remove price alert
        
        Args:
            alert_id: Alert ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            self.stats["active_alerts"] = len([a for a in self.alerts.values() if not a.triggered])
            logger.info(f"Removed alert: {alert_id}")
            return True
        return False
    
    def get_alert(self, alert_id: str) -> Optional[Dict]:
        """Get alert by ID"""
        alert = self.alerts.get(alert_id)
        return alert.to_dict() if alert else None
    
    def list_alerts(self, active_only: bool = False) -> List[Dict]:
        """
        List all alerts
        
        Args:
            active_only: Only return non-triggered alerts
            
        Returns:
            List of alert dictionaries
        """
        alerts = self.alerts.values()
        if active_only:
            alerts = [a for a in alerts if not a.triggered]
        return [a.to_dict() for a in alerts]
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Get unique symbols from active alerts
                active_alerts = [a for a in self.alerts.values() if not a.triggered]
                symbols = set(a.symbol for a in active_alerts)
                
                if not symbols:
                    # No active alerts, wait longer
                    await asyncio.sleep(self.poll_interval * 2)
                    continue
                
                # Fetch current prices
                prices = await self._fetch_prices(symbols)
                
                # Check each alert
                triggered_alerts = []
                for alert in active_alerts:
                    current_price = prices.get(alert.symbol)
                    
                    if current_price is None:
                        continue
                    
                    # Check if alert is triggered
                    trigger_type = alert.check_price(current_price)
                    
                    if trigger_type:
                        logger.info(f"Alert triggered: {alert.symbol} {trigger_type} at {current_price}")
                        
                        # Update statistics
                        self.stats["triggered_alerts"] += 1
                        if trigger_type == "VALIDATION":
                            self.stats["validations"] += 1
                        else:
                            self.stats["invalidations"] += 1
                        
                        # Add to triggered list
                        triggered_alerts.append(alert)
                
                # Update active alerts count
                self.stats["active_alerts"] = len([a for a in self.alerts.values() if not a.triggered])
                
                # Broadcast triggered alerts
                if triggered_alerts:
                    await self._broadcast_alerts(triggered_alerts)
                    
                    # Call alert callback if provided
                    if self.alert_callback:
                        await self._notify_agent(triggered_alerts)
                
                # Wait before next poll
                await asyncio.sleep(self.poll_interval)
            
            except Exception as e:
                logger.error(f"Monitor loop error: {e}", exc_info=True)
                await asyncio.sleep(30)  # Wait 30 seconds on error
    
    async def _fetch_prices(self, symbols: Set[str]) -> Dict[str, float]:
        """
        Fetch current prices for symbols from WebSocket market handler
        
        Args:
            symbols: Set of symbols to fetch
            
        Returns:
            Dictionary of symbol -> price
        """
        prices = {}
        
        try:
            # Get prices from market handler (Drift/Backpack WebSocket)
            for symbol in symbols:
                symbol_upper = symbol.upper()
                price_update = self.market_handler.get_price(symbol_upper)
                
                if price_update and price_update.price:
                    prices[symbol_upper] = price_update.price
                    
                    # Update cache
                    self.price_cache[symbol_upper] = {
                        "price": price_update.price,
                        "timestamp": datetime.now()
                    }
                else:
                    logger.warning(f"No price data available for {symbol_upper}")
            
            if prices:
                self.stats["price_checks"] += 1
            
        except Exception as e:
            logger.error(f"Fetch prices error: {e}")
        
        return prices
    
    async def _broadcast_alerts(self, alerts: List[PriceAlert]):
        """Broadcast triggered alerts to all subscribers"""
        if not self.subscribers:
            return
        
        message = {
            "type": "price_alert",
            "timestamp": datetime.now().isoformat(),
            "count": len(alerts),
            "alerts": [a.to_dict() for a in alerts]
        }
        
        # Send to all subscribers
        dead_queues = []
        for queue in self.subscribers:
            try:
                await queue.put(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                dead_queues.append(queue)
        
        # Remove dead queues
        for queue in dead_queues:
            self.unsubscribe(queue)
    
    async def _notify_agent(self, alerts: List[PriceAlert]):
        """Notify agent about triggered alerts"""
        try:
            for alert in alerts:
                # Build notification message
                if alert.trigger_type == "VALIDATION":
                    message = f"""🎯 VALIDATION TRIGGERED!

Symbol: {alert.symbol}
Direction: {alert.direction}
Validation Price: ${alert.validation_price:,.2f}
Current Price: ${alert.trigger_price:,.2f}
Time: {alert.trigger_time.strftime('%Y-%m-%d %H:%M:%S')}

✅ Price reached validation level. Trade setup is valid!"""
                else:  # INVALIDATION
                    message = f"""⚠️ INVALIDATION TRIGGERED!

Symbol: {alert.symbol}
Direction: {alert.direction}
Invalidation Price: ${alert.invalidation_price:,.2f}
Current Price: ${alert.trigger_price:,.2f}
Time: {alert.trigger_time.strftime('%Y-%m-%d %H:%M:%S')}

❌ Price reached invalidation level. Trade setup is invalid!"""
                
                # Call alert callback
                if self.alert_callback:
                    await self.alert_callback(message)
        
        except Exception as e:
            logger.error(f"Notify agent error: {e}")
    
    def get_stats(self) -> Dict:
        """Get monitor statistics"""
        return {
            "running": self.running,
            "poll_interval": self.poll_interval,
            "subscribers": len(self.subscribers),
            "cached_prices": len(self.price_cache),
            **self.stats
        }
    
    def set_alert_callback(self, callback: Callable):
        """Set alert callback function"""
        self.alert_callback = callback
        logger.info("Alert callback set")
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get cached current price for symbol"""
        cached = self.price_cache.get(symbol.upper())
        if cached:
            return cached["price"]
        return None


# Singleton instance
_price_monitor: Optional[PriceMonitor] = None


def get_price_monitor() -> PriceMonitor:
    """Get or create PriceMonitor singleton"""
    global _price_monitor
    if _price_monitor is None:
        _price_monitor = PriceMonitor()
    return _price_monitor
