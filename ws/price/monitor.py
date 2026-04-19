"""
Price WebSocket Monitor
Real-time price monitoring with validation/invalidation alerts.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set

from agents.service_costs import get_monitoring_cost_service
from ws.handlers.market_handler import MarketDataHandler

logger = logging.getLogger(__name__)

PriceAlertCallback = Callable[[Dict[str, Any]], Awaitable[None]]


class PriceAlert:
    """Price alert configuration and trigger event formatting."""

    def __init__(
        self,
        alert_id: str,
        symbol: str,
        validation_price: float,
        invalidation_price: float,
        direction: str = "LONG",
        exchange: str = "drift",
        trade_label: Optional[str] = None,
        trade_id: Optional[str] = None,
        setup_id: Optional[str] = None,
        scope_id: Optional[str] = None,
        user_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        self.alert_id = alert_id
        self.symbol = symbol.upper()
        self.validation_price = validation_price
        self.invalidation_price = invalidation_price
        self.direction = direction.upper()
        self.exchange = exchange.lower()
        self.trade_label = trade_label.strip() if isinstance(trade_label, str) and trade_label.strip() else None
        self.trade_id = trade_id.strip() if isinstance(trade_id, str) and trade_id.strip() else None
        self.setup_id = setup_id.strip() if isinstance(setup_id, str) and setup_id.strip() else None
        self.scope_id = scope_id.strip() if isinstance(scope_id, str) and scope_id.strip() else None
        self.user_id = user_id.strip() if isinstance(user_id, str) and user_id.strip() else None
        self.created_at = created_at or datetime.now()
        self.triggered = False
        self.trigger_type: Optional[str] = None
        self.trigger_price: Optional[float] = None
        self.trigger_time: Optional[datetime] = None

    def check_price(self, current_price: float) -> Optional[str]:
        """
        Check if price triggers validation or invalidation.

        Returns:
            "VALIDATION" or "INVALIDATION" if triggered, None otherwise.
        """
        if self.triggered:
            return None

        if self.direction == "LONG":
            if current_price >= self.validation_price:
                self.triggered = True
                self.trigger_type = "VALIDATION"
                self.trigger_price = current_price
                self.trigger_time = datetime.now()
                return "VALIDATION"
            if current_price <= self.invalidation_price:
                self.triggered = True
                self.trigger_type = "INVALIDATION"
                self.trigger_price = current_price
                self.trigger_time = datetime.now()
                return "INVALIDATION"

        if self.direction == "SHORT":
            if current_price <= self.validation_price:
                self.triggered = True
                self.trigger_type = "VALIDATION"
                self.trigger_price = current_price
                self.trigger_time = datetime.now()
                return "VALIDATION"
            if current_price >= self.invalidation_price:
                self.triggered = True
                self.trigger_type = "INVALIDATION"
                self.trigger_price = current_price
                self.trigger_time = datetime.now()
                return "INVALIDATION"

        return None

    def _reference_label(self) -> str:
        if self.trade_label:
            return self.trade_label
        if self.setup_id:
            return self.setup_id
        if self.trade_id:
            return self.trade_id
        return f"{self.symbol} {self.direction} setup"

    def build_default_prompt(self, trigger_type: str, trigger_price: float) -> str:
        """Build the default prompt that frontend or orchestrators can reuse."""
        return (
            f"{self._reference_label()} hit {trigger_type.lower()} price at "
            f"${trigger_price:,.2f} on {self.exchange.upper()} for {self.symbol}."
        )

    def preview_prompt(self, trigger_type: str) -> str:
        """Build a preview prompt from configured thresholds before trigger time."""
        trigger_type = trigger_type.upper()
        trigger_price = self.validation_price if trigger_type == "VALIDATION" else self.invalidation_price
        return self.build_default_prompt(trigger_type, trigger_price)

    def build_trigger_event(self) -> Dict[str, Any]:
        """Build the structured event payload emitted when the alert triggers."""
        default_prompt = self.build_default_prompt(self.trigger_type or "VALIDATION", self.trigger_price or 0.0)
        return {
            "type": "price_alert_triggered",
            "timestamp": (self.trigger_time or datetime.now()).isoformat(),
            "alert_id": self.alert_id,
            "symbol": self.symbol,
            "direction": self.direction,
            "exchange": self.exchange,
            "scope_id": self.scope_id,
            "user_id": self.user_id,
            "trade_label": self.trade_label,
            "trade_id": self.trade_id,
            "setup_id": self.setup_id,
            "validation_price": self.validation_price,
            "invalidation_price": self.invalidation_price,
            "trigger_type": self.trigger_type,
            "trigger_price": self.trigger_price,
            "trigger_time": self.trigger_time.isoformat() if self.trigger_time else None,
            "default_prompt": default_prompt,
            "message": default_prompt,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to a serializable dictionary."""
        return {
            "alert_id": self.alert_id,
            "symbol": self.symbol,
            "validation_price": self.validation_price,
            "invalidation_price": self.invalidation_price,
            "direction": self.direction,
            "exchange": self.exchange,
            "scope_id": self.scope_id,
            "user_id": self.user_id,
            "trade_label": self.trade_label,
            "trade_id": self.trade_id,
            "setup_id": self.setup_id,
            "created_at": self.created_at.isoformat(),
            "triggered": self.triggered,
            "trigger_type": self.trigger_type,
            "trigger_price": self.trigger_price,
            "trigger_time": self.trigger_time.isoformat() if self.trigger_time else None,
            "default_prompt": (
                self.build_default_prompt(self.trigger_type, self.trigger_price)
                if self.triggered and self.trigger_type and self.trigger_price is not None
                else None
            ),
        }


class PriceMonitor:
    """
    Real-time price monitor with validation/invalidation alerts.

    It polls for live price updates and emits a structured event that frontend
    or orchestrators can use directly as a notification or chat prefill.
    """

    def __init__(
        self,
        poll_interval: int = 10,
        alert_callback: Optional[PriceAlertCallback] = None,
        market_handler: Optional[MarketDataHandler] = None,
    ):
        self.poll_interval = poll_interval
        self.alert_callback = alert_callback

        self.running = False
        self.alerts: Dict[str, PriceAlert] = {}
        self.subscribers: Set[asyncio.Queue] = set()

        if market_handler:
            self.market_handler = market_handler
        else:
            from ws.handlers import get_market_handler

            self.market_handler = get_market_handler()

        self.price_cache: Dict[str, Dict[str, Any]] = {}
        self.stats = {
            "total_alerts": 0,
            "active_alerts": 0,
            "triggered_alerts": 0,
            "validations": 0,
            "invalidations": 0,
            "price_checks": 0,
        }

        logger.info("Price monitor initialized (poll: %ss)", poll_interval)

    async def start(self):
        """Start monitoring prices."""
        if self.running:
            logger.warning("Price monitor already running")
            return

        self.running = True
        logger.info("Price monitor started")
        asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """Stop monitoring prices."""
        self.running = False
        logger.info("Price monitor stopped")

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to triggered price-alert events."""
        queue = asyncio.Queue()
        self.subscribers.add(queue)
        logger.info("New subscriber added (total: %s)", len(self.subscribers))
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from triggered price-alert events."""
        if queue in self.subscribers:
            self.subscribers.remove(queue)
            logger.info("Subscriber removed (total: %s)", len(self.subscribers))

    def add_alert(
        self,
        symbol: str,
        validation_price: float,
        invalidation_price: float,
        direction: str = "LONG",
        exchange: str = "drift",
        alert_id: Optional[str] = None,
        trade_label: Optional[str] = None,
        trade_id: Optional[str] = None,
        setup_id: Optional[str] = None,
        scope_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Add a price alert.

        Args:
            symbol: Trading symbol (e.g., BTC, ETH)
            validation_price: Price level for validation
            invalidation_price: Price level for invalidation
            direction: Trade direction (LONG or SHORT)
            exchange: Exchange to monitor (drift, backpack, binance)
            alert_id: Optional custom alert ID
            trade_label: Optional user-facing trade label
            trade_id: Optional trade reference ID
            setup_id: Optional setup reference ID
            scope_id: Optional scope ID for ownership and cost tracking
            user_id: Optional user ID for ownership and cost tracking
        """
        if not alert_id:
            alert_id = f"{symbol}_{direction}_{exchange}_{datetime.now().timestamp()}"

        if direction.upper() not in ["LONG", "SHORT"]:
            raise ValueError("Direction must be LONG or SHORT")

        if exchange.lower() not in ["drift", "backpack", "binance"]:
            raise ValueError("Exchange must be drift, backpack, or binance")

        if direction.upper() == "LONG":
            if validation_price <= invalidation_price:
                raise ValueError("For LONG: validation_price must be > invalidation_price")
        elif validation_price >= invalidation_price:
            raise ValueError("For SHORT: validation_price must be < invalidation_price")

        alert = PriceAlert(
            alert_id=alert_id,
            symbol=symbol,
            validation_price=validation_price,
            invalidation_price=invalidation_price,
            direction=direction,
            exchange=exchange,
            trade_label=trade_label,
            trade_id=trade_id,
            setup_id=setup_id,
            scope_id=scope_id,
            user_id=user_id,
        )

        self.alerts[alert_id] = alert
        self.stats["total_alerts"] += 1
        self.stats["active_alerts"] = len([item for item in self.alerts.values() if not item.triggered])

        logger.info(
            "Added alert: %s %s on %s | Val: %s | Inval: %s | Label: %s",
            symbol,
            direction,
            exchange,
            validation_price,
            invalidation_price,
            trade_label,
        )

        get_monitoring_cost_service().record_alert_started(
            scope_id=scope_id,
            user_id=user_id,
            alert_id=alert_id,
            symbol=alert.symbol,
            exchange=alert.exchange,
            direction=alert.direction,
            started_at=alert.created_at.isoformat(),
            metadata={
                "trade_label": alert.trade_label,
                "trade_id": alert.trade_id,
                "setup_id": alert.setup_id,
            },
        )

        return alert_id

    def _alert_matches_owner(
        self,
        alert: PriceAlert,
        *,
        scope_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """Return whether one alert belongs to the requested owner context."""
        if scope_id and alert.scope_id:
            return alert.scope_id == scope_id
        if user_id and alert.user_id:
            return alert.user_id == user_id
        if scope_id:
            return alert.scope_id == scope_id
        if user_id:
            return alert.user_id == user_id
        return True

    def remove_alert(
        self,
        alert_id: str,
        *,
        scope_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """Remove a price alert."""
        alert = self.alerts.get(alert_id)
        if alert and self._alert_matches_owner(alert, scope_id=scope_id, user_id=user_id):
            if not alert.triggered:
                get_monitoring_cost_service().record_alert_removed(
                    scope_id=alert.scope_id,
                    alert_id=alert.alert_id,
                    removed_at=datetime.now().isoformat(),
                )
            del self.alerts[alert_id]
            self.stats["active_alerts"] = len([item for item in self.alerts.values() if not item.triggered])
            logger.info("Removed alert: %s", alert_id)
            return True
        return False

    def get_alert(
        self,
        alert_id: str,
        *,
        scope_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get one alert by ID."""
        alert = self.alerts.get(alert_id)
        if not alert or not self._alert_matches_owner(alert, scope_id=scope_id, user_id=user_id):
            return None
        return alert.to_dict()

    def list_alerts(
        self,
        active_only: bool = False,
        *,
        scope_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List alerts, optionally only active ones."""
        alerts = [
            item
            for item in self.alerts.values()
            if self._alert_matches_owner(item, scope_id=scope_id, user_id=user_id)
        ]
        if active_only:
            alerts = [item for item in alerts if not item.triggered]
        return [item.to_dict() for item in alerts]

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                active_alerts = [alert for alert in self.alerts.values() if not alert.triggered]
                symbols = {alert.symbol for alert in active_alerts}

                if not symbols:
                    await asyncio.sleep(self.poll_interval * 2)
                    continue

                prices = await self._fetch_prices(symbols)

                triggered_alerts: List[PriceAlert] = []
                for alert in active_alerts:
                    current_price = prices.get(alert.symbol)
                    if current_price is None:
                        continue

                    trigger_type = alert.check_price(current_price)
                    if not trigger_type:
                        continue

                    logger.info("Alert triggered: %s %s at %s", alert.symbol, trigger_type, current_price)
                    self.stats["triggered_alerts"] += 1
                    if trigger_type == "VALIDATION":
                        self.stats["validations"] += 1
                    else:
                        self.stats["invalidations"] += 1
                    get_monitoring_cost_service().record_alert_triggered(
                        scope_id=alert.scope_id,
                        alert_id=alert.alert_id,
                        triggered_at=alert.trigger_time.isoformat() if alert.trigger_time else datetime.now().isoformat(),
                        trigger_type=alert.trigger_type,
                        trigger_price=alert.trigger_price,
                    )
                    triggered_alerts.append(alert)

                self.stats["active_alerts"] = len([alert for alert in self.alerts.values() if not alert.triggered])

                if triggered_alerts:
                    await self._broadcast_alerts(triggered_alerts)
                    if self.alert_callback:
                        await self._notify_agent(triggered_alerts)

                await asyncio.sleep(self.poll_interval)

            except Exception as e:
                logger.error("Monitor loop error: %s", e, exc_info=True)
                await asyncio.sleep(30)

    async def _fetch_prices(self, symbols: Set[str]) -> Dict[str, float]:
        """Fetch current prices for tracked symbols."""
        prices: Dict[str, float] = {}

        try:
            for symbol in symbols:
                symbol_upper = symbol.upper()
                price_update = self.market_handler.get_price(symbol_upper)
                if price_update and price_update.price:
                    prices[symbol_upper] = price_update.price
                    self.price_cache[symbol_upper] = {
                        "price": price_update.price,
                        "timestamp": datetime.now(),
                    }
                else:
                    logger.warning("No price data available for %s", symbol_upper)

            if prices:
                self.stats["price_checks"] += 1
        except Exception as e:
            logger.error("Fetch prices error: %s", e)

        return prices

    async def _broadcast_alerts(self, alerts: List[PriceAlert]):
        """Broadcast triggered alerts to all subscribers."""
        if not self.subscribers:
            return

        message = {
            "type": "price_alert_triggered",
            "timestamp": datetime.now().isoformat(),
            "count": len(alerts),
            "alerts": [alert.build_trigger_event() for alert in alerts],
        }

        dead_queues = []
        for queue in self.subscribers:
            try:
                await queue.put(message)
            except Exception as e:
                logger.error("Broadcast error: %s", e)
                dead_queues.append(queue)

        for queue in dead_queues:
            self.unsubscribe(queue)

    async def _notify_agent(self, alerts: List[PriceAlert]):
        """Notify agent or automation layer about triggered alerts."""
        try:
            for alert in alerts:
                if self.alert_callback:
                    await self.alert_callback(alert.build_trigger_event())
        except Exception as e:
            logger.error("Notify agent error: %s", e)

    def get_stats(
        self,
        *,
        scope_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get monitor statistics."""
        filtered_alerts = [
            item
            for item in self.alerts.values()
            if self._alert_matches_owner(item, scope_id=scope_id, user_id=user_id)
        ]
        active_alerts = [item for item in filtered_alerts if not item.triggered]
        triggered_alerts = [item for item in filtered_alerts if item.triggered]
        validations = [item for item in triggered_alerts if item.trigger_type == "VALIDATION"]
        invalidations = [item for item in triggered_alerts if item.trigger_type == "INVALIDATION"]
        return {
            "running": self.running,
            "poll_interval": self.poll_interval,
            "subscribers": len(self.subscribers),
            "cached_prices": len(self.price_cache),
            "total_alerts": len(filtered_alerts),
            "active_alerts": len(active_alerts),
            "triggered_alerts": len(triggered_alerts),
            "validations": len(validations),
            "invalidations": len(invalidations),
            "price_checks": self.stats["price_checks"],
        }

    def set_alert_callback(self, callback: PriceAlertCallback):
        """Set callback for triggered alerts."""
        self.alert_callback = callback
        logger.info("Alert callback set")

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get cached current price for a symbol."""
        cached = self.price_cache.get(symbol.upper())
        if cached:
            return cached["price"]
        return None


_price_monitor: Optional[PriceMonitor] = None


def get_price_monitor() -> PriceMonitor:
    """Get or create PriceMonitor singleton."""
    global _price_monitor
    if _price_monitor is None:
        _price_monitor = PriceMonitor()
    return _price_monitor
