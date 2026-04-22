"""Price monitoring tools for trading agent"""
from typing import Dict, Any, List, Optional

from agents.service_costs import get_monitoring_cost_service
from agents.tools.core.runtime_context import get_current_scope_id, get_current_user_id
from ws.price.monitor import get_price_monitor
from utils.logger import get_logger

logger = get_logger(__name__)


async def add_price_alert(
    symbol: str,
    validation_price: float,
    invalidation_price: float,
    direction: str = "LONG",
    exchange: str = "phantom",
    trade_label: Optional[str] = None,
    trade_id: Optional[str] = None,
    setup_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Add price alert for validation/invalidation monitoring
    
    Args:
        symbol: Trading symbol (BTC, ETH, SOL, etc.)
        validation_price: Price level that validates the trade setup
        invalidation_price: Price level that invalidates the trade setup
        direction: Trade direction - LONG or SHORT
            - LONG: validation_price > current > invalidation_price
            - SHORT: validation_price < current < invalidation_price
        exchange: Exchange to monitor - "phantom", "spot", or "futures" (default: "phantom")
        trade_label: Optional human-friendly label like "Trade A" or "SOL breakout setup"
        trade_id: Optional trade reference ID
        setup_id: Optional setup reference ID
    
    Returns:
        Alert details with alert_id
        
    Example:
        # LONG setup: BTC breaks above 95000 (validation) or below 90000 (invalidation)
        add_price_alert("BTC", validation_price=95000, invalidation_price=90000, direction="LONG", exchange="phantom")
        
        # SHORT setup: ETH breaks below 3000 (validation) or above 3200 (invalidation)
        add_price_alert("ETH", validation_price=3000, invalidation_price=3200, direction="SHORT", exchange="spot")
    """
    try:
        # Validate inputs
        if not symbol or not isinstance(symbol, str):
            return {
                "success": False,
                "error": "Symbol must be a non-empty string",
                "provided": symbol,
                "suggestion": "Use symbols like 'BTC', 'ETH', 'SOL', etc."
            }
        
        symbol = symbol.upper().strip()
        
        # Validate exchange
        exchange_aliases = {
            "phantom": "phantom",
            "futures": "futures",
            "spot": "spot",
        }
        valid_exchanges = list(exchange_aliases.keys())
        if exchange.lower() not in valid_exchanges:
            return {
                "success": False,
                "error": f"Invalid exchange: '{exchange}'",
                "provided": exchange,
                "valid_options": valid_exchanges,
                "suggestion": "Use 'phantom', 'spot', or 'futures'"
            }
        
        exchange = exchange_aliases[exchange.lower()]
        
        # Validate direction
        if direction.upper() not in ["LONG", "SHORT"]:
            return {
                "success": False,
                "error": f"Invalid direction: '{direction}'",
                "provided": direction,
                "valid_options": ["LONG", "SHORT"],
                "suggestion": "Use 'LONG' for bullish setups or 'SHORT' for bearish setups"
            }
        
        # Validate prices
        try:
            validation_price = float(validation_price)
            invalidation_price = float(invalidation_price)
        except (ValueError, TypeError):
            return {
                "success": False,
                "error": "Prices must be numeric values",
                "provided": {
                    "validation_price": validation_price,
                    "invalidation_price": invalidation_price
                },
                "suggestion": "Provide valid numeric prices, e.g., 95000.50"
            }
        
        # Get monitor
        monitor = get_price_monitor()
        current_scope_id = get_current_scope_id()
        current_user_id = get_current_user_id()
        
        # Add alert with exchange info
        alert_id = monitor.add_alert(
            symbol=symbol,
            validation_price=validation_price,
            invalidation_price=invalidation_price,
            direction=direction.upper(),
            exchange=exchange,
            trade_label=trade_label,
            trade_id=trade_id,
            setup_id=setup_id,
            scope_id=current_scope_id,
            user_id=current_user_id,
        )
        monitoring_cost = (
            get_monitoring_cost_service().get_scope_summary(scope_id=current_scope_id)
            if current_scope_id
            else None
        )
        
        # Get current price
        current_price = monitor.get_current_price(symbol)
        
        logger.info(f"Added price alert: {symbol} {direction} on {exchange} | Val: {validation_price} | Inval: {invalidation_price}")

        trade_reference = trade_label or setup_id or trade_id or f"{symbol} {direction.upper()} setup"

        return {
            "success": True,
            "alert_id": alert_id,
            "symbol": symbol,
            "direction": direction.upper(),
            "exchange": exchange,
            "trade_label": trade_label,
            "trade_id": trade_id,
            "setup_id": setup_id,
            "validation_price": validation_price,
            "invalidation_price": invalidation_price,
            "current_price": current_price,
            "scope_id": current_scope_id,
            "user_id": current_user_id,
            "message": f"Price alert added for {symbol} {direction.upper()} setup on {exchange}",
            "monitoring": f"Will alert when price reaches ${validation_price:,.2f} (validation) or ${invalidation_price:,.2f} (invalidation)",
            "default_prompts": {
                "validation": f"{trade_reference} hit validation price at ${validation_price:,.2f} on {exchange.upper()} for {symbol}.",
                "invalidation": f"{trade_reference} hit invalidation price at ${invalidation_price:,.2f} on {exchange.upper()} for {symbol}.",
            },
            "monitor_cost": monitoring_cost,
        }
    
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "suggestion": "Check that validation and invalidation prices are correct for the direction"
        }
    except Exception as e:
        logger.error(f"Add price alert error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to add price alert: {str(e)}"
        }


async def remove_price_alert(alert_id: str) -> Dict[str, Any]:
    """
    Remove price alert
    
    Args:
        alert_id: Alert ID to remove
        
    Returns:
        Success status
    """
    try:
        if not alert_id or not isinstance(alert_id, str):
            return {
                "success": False,
                "error": "Alert ID must be a non-empty string",
                "provided": alert_id,
                "suggestion": "Get alert_id from list_price_alerts() first"
            }
        
        monitor = get_price_monitor()
        removed = monitor.remove_alert(
            alert_id,
            scope_id=get_current_scope_id(),
            user_id=get_current_user_id(),
        )
        
        if removed:
            logger.info(f"Removed price alert: {alert_id}")
            return {
                "success": True,
                "alert_id": alert_id,
                "message": f"Price alert {alert_id} removed"
            }
        else:
            return {
                "success": False,
                "error": f"Alert not found: {alert_id}",
                "suggestion": "Use list_price_alerts() to see available alerts"
            }
    
    except Exception as e:
        logger.error(f"Remove price alert error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to remove price alert: {str(e)}"
        }


async def list_price_alerts(active_only: bool = False) -> Dict[str, Any]:
    """
    List all price alerts
    
    Args:
        active_only: Only return non-triggered alerts (default: False)
        
    Returns:
        List of alerts with details
    """
    try:
        monitor = get_price_monitor()
        alerts = monitor.list_alerts(
            active_only=active_only,
            scope_id=get_current_scope_id(),
            user_id=get_current_user_id(),
        )
        
        # Separate by status
        active = [a for a in alerts if not a["triggered"]]
        triggered = [a for a in alerts if a["triggered"]]
        
        # Separate triggered by type
        validations = [a for a in triggered if a["trigger_type"] == "VALIDATION"]
        invalidations = [a for a in triggered if a["trigger_type"] == "INVALIDATION"]
        
        return {
            "success": True,
            "total_alerts": len(alerts),
            "active_alerts": len(active),
            "triggered_alerts": len(triggered),
            "validations": len(validations),
            "invalidations": len(invalidations),
            "alerts": alerts,
            "summary": f"Found {len(alerts)} alerts ({len(active)} active, {len(triggered)} triggered)"
        }
    
    except Exception as e:
        logger.error(f"List price alerts error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to list price alerts: {str(e)}"
        }


async def get_price_alert(alert_id: str) -> Dict[str, Any]:
    """
    Get specific price alert details
    
    Args:
        alert_id: Alert ID
        
    Returns:
        Alert details
    """
    try:
        if not alert_id or not isinstance(alert_id, str):
            return {
                "success": False,
                "error": "Alert ID must be a non-empty string",
                "provided": alert_id
            }
        
        monitor = get_price_monitor()
        alert = monitor.get_alert(
            alert_id,
            scope_id=get_current_scope_id(),
            user_id=get_current_user_id(),
        )
        
        if alert:
            return {
                "success": True,
                "alert": alert
            }
        else:
            return {
                "success": False,
                "error": f"Alert not found: {alert_id}",
                "suggestion": "Use list_price_alerts() to see available alerts"
            }
    
    except Exception as e:
        logger.error(f"Get price alert error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to get price alert: {str(e)}"
        }


async def get_price_monitor_stats() -> Dict[str, Any]:
    """
    Get price monitor statistics
    
    Returns:
        Monitor statistics and status
    """
    try:
        monitor = get_price_monitor()
        stats = monitor.get_stats(
            scope_id=get_current_scope_id(),
            user_id=get_current_user_id(),
        )
        monitoring_cost = (
            get_monitoring_cost_service().get_scope_summary(scope_id=get_current_scope_id())
            if get_current_scope_id()
            else None
        )
        
        return {
            "success": True,
            "stats": stats,
            "monitor_cost": monitoring_cost,
            "summary": f"Monitor is {'running' if stats['running'] else 'stopped'} with {stats['active_alerts']} active alerts"
        }
    
    except Exception as e:
        logger.error(f"Get price monitor stats error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to get monitor stats: {str(e)}"
        }


async def start_price_monitor() -> Dict[str, Any]:
    """
    Start price monitoring
    
    Returns:
        Success status
    """
    try:
        monitor = get_price_monitor()
        await monitor.start()
        
        logger.info("Price monitor started")
        
        return {
            "success": True,
            "message": "Price monitor started",
            "poll_interval": monitor.poll_interval
        }
    
    except Exception as e:
        logger.error(f"Start price monitor error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to start price monitor: {str(e)}"
        }


async def stop_price_monitor() -> Dict[str, Any]:
    """
    Stop price monitoring
    
    Returns:
        Success status
    """
    try:
        monitor = get_price_monitor()
        await monitor.stop()
        
        logger.info("Price monitor stopped")
        
        return {
            "success": True,
            "message": "Price monitor stopped"
        }
    
    except Exception as e:
        logger.error(f"Stop price monitor error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to stop price monitor: {str(e)}"
        }
