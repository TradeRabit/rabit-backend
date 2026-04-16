"""Trading tools for Rabit Agent"""
from agents.tools import tool_registry, ToolDefinition, ToolParameter
from utils.logger import get_logger
from ws.handlers import MarketDataHandler
from agents.tools.web_search import web_search
from agents.tools.news_tools import (
    get_latest_news,
    search_news_by_keywords,
    get_trending_news,
    search_news_by_symbols,
    start_news_monitoring,
    stop_news_monitoring,
    get_monitoring_status
)
from agents.tools.tradingview_tools import register_tradingview_tools
from agents.tools.price_monitor_tools import (
    add_price_alert,
    remove_price_alert,
    list_price_alerts,
    get_price_alert,
    get_price_monitor_stats,
    start_price_monitor,
    stop_price_monitor
)

logger = get_logger(__name__)

# Global market handler instance
_market_handler = None

def get_market_handler() -> MarketDataHandler:
    """Get or create market handler singleton"""
    global _market_handler
    if _market_handler is None:
        _market_handler = MarketDataHandler()
    return _market_handler


# Tool: Get Price
async def get_price(symbol: str) -> dict:
    """
    Get real-time market price for a symbol
    
    Args:
        symbol: Trading symbol (e.g., SOL, BTC, ETH)
        
    Returns:
        Real-time price information from WebSocket
    """
    logger.info(f"Getting real-time price for {symbol}")
    
    # Normalize symbol to uppercase
    symbol = symbol.upper()
    
    # Get market handler
    handler = get_market_handler()
    
    # Get price from handler
    price_update = handler.get_price(symbol)
    
    if not price_update:
        return {
            "success": False,
            "error": f"Price data not available for {symbol}",
            "symbol": symbol,
            "suggestion": "Make sure WebSocket is connected and symbol is valid. Available symbols: BTC, ETH, SOL, DOGE, BNB, SUI, APT, ARB, RENDER, XRP, INJ, LINK, PYTH, JTO, AVAX, WIF, JUP, TAO, KMNO, TNSR, DRIFT, RAY, HYPE, LTC, FARTCOIN"
        }
    
    return {
        "success": True,
        "symbol": price_update.symbol,
        "price": price_update.price,
        "change_24h": price_update.change_24h,
        "volume_24h": price_update.volume_24h,
        "high_24h": price_update.high_24h,
        "low_24h": price_update.low_24h,
        "market_cap": price_update.market_cap,
        "fdv": price_update.fdv,
        "open_interest": price_update.open_interest,
        "funding_rate": price_update.funding_rate,
        "timestamp": price_update.timestamp.isoformat()
    }


def register_trading_tools():
    """Register trading tools to the registry"""
    
    # Register get_price
    tool_registry.register(ToolDefinition(
        name="get_price",
        description="Get real-time market price for a trading symbol from WebSocket data. Returns current price, 24h change, volume, high/low, market cap, FDV, open interest, and funding rate.",
        parameters=[
            ToolParameter(
                name="symbol",
                type="string",
                description="Trading symbol in uppercase (e.g., SOL, BTC, ETH, DOGE, BNB, SUI, APT, ARB, RENDER, XRP, INJ, LINK, PYTH, JTO, AVAX, WIF, JUP, TAO, KMNO, TNSR, DRIFT, RAY, HYPE, LTC, FARTCOIN)",
                required=True
            )
        ],
        function=get_price
    ))
    
    # Register web_search
    tool_registry.register(ToolDefinition(
        name="web_search",
        description="Search the web for information about crypto, markets, news, or any topic. Returns minimal results with title, URL, and brief snippet. Use for: market news, crypto analysis, price predictions, trading strategies, or general information.",
        parameters=[
            ToolParameter(
                name="query",
                type="string",
                description="Search query (e.g., 'Bitcoin price prediction 2024', 'Ethereum news today', 'Solana DeFi projects')",
                required=True
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of results to return (default: 5, max: 10)",
                required=False
            )
        ],
        function=web_search
    ))
    
    # Register get_latest_news
    tool_registry.register(ToolDefinition(
        name="get_latest_news",
        description="Get latest news from specific category. Categories: crypto (default), general, finance, defi, nft. Returns news with title, URL, snippet, date, and source.",
        parameters=[
            ToolParameter(
                name="category",
                type="string",
                description="News category: crypto, general, finance, defi, nft (default: crypto)",
                required=False
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of results (default: 10)",
                required=False
            )
        ],
        function=get_latest_news
    ))
    
    # Register search_news_by_keywords
    tool_registry.register(ToolDefinition(
        name="search_news_by_keywords",
        description="Search news by keywords with REGEX support. Use pipe (|) for OR logic: 'BTC|ETH|TRUMP' finds news mentioning any of these. Perfect for multi-symbol monitoring or tracking multiple topics.",
        parameters=[
            ToolParameter(
                name="keywords",
                type="string",
                description="Keywords to search. Supports regex: 'BTC|ETH|SOL' (OR logic), 'bitcoin.*price' (pattern matching), '(pump|dump)' (grouping)",
                required=True
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of results (default: 10)",
                required=False
            )
        ],
        function=search_news_by_keywords
    ))
    
    # Register get_trending_news
    tool_registry.register(ToolDefinition(
        name="get_trending_news",
        description="Get trending crypto news. Returns most discussed and recent news about price movements, hacks, regulations, and developments. Cached for 5 minutes for performance.",
        parameters=[
            ToolParameter(
                name="timeframe",
                type="string",
                description="Time frame: 24h (default), 7d, 30d",
                required=False
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of results (default: 10)",
                required=False
            )
        ],
        function=get_trending_news
    ))
    
    # Register search_news_by_symbols
    tool_registry.register(ToolDefinition(
        name="search_news_by_symbols",
        description="Search news for multiple trading symbols at once. Returns news grouped by symbol. Useful for portfolio monitoring or comparing news across assets.",
        parameters=[
            ToolParameter(
                name="symbols",
                type="string",
                description="Comma-separated symbols (e.g., 'BTC,ETH,SOL,DOGE')",
                required=True
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum results per symbol (default: 5)",
                required=False
            )
        ],
        function=search_news_by_symbols
    ))
    
    # Register start_news_monitoring
    tool_registry.register(ToolDefinition(
        name="start_news_monitoring",
        description="Start real-time news monitoring with automatic AI review. Monitor will poll for new news, analyze sentiment (POSITIVE/NEGATIVE/NEUTRAL), assess impact (HIGH/MEDIUM/LOW), and provide trading recommendations (BUY/SELL/HOLD). Perfect for trading on news - get alerts when bad news (sell signal) or good news (buy signal) appears.",
        parameters=[
            ToolParameter(
                name="keywords",
                type="string",
                description="Keywords to monitor (supports regex like 'BTC|ETH|SOL'). Separate multiple patterns with commas.",
                required=False
            ),
            ToolParameter(
                name="poll_interval",
                type="number",
                description="Polling interval in seconds (default: 300 = 5 minutes, min: 60)",
                required=False
            )
        ],
        function=start_news_monitoring
    ))
    
    # Register stop_news_monitoring
    tool_registry.register(ToolDefinition(
        name="stop_news_monitoring",
        description="Stop real-time news monitoring. Returns final statistics including total news found, sentiment breakdown, and review counts.",
        parameters=[],
        function=stop_news_monitoring
    ))
    
    # Register get_monitoring_status
    tool_registry.register(ToolDefinition(
        name="get_monitoring_status",
        description="Get current news monitoring status and statistics. Shows if monitoring is running, keywords being tracked, subscriber count, and sentiment analysis stats (positive/negative/neutral news counts).",
        parameters=[],
        function=get_monitoring_status
    ))
    
    # ===== PRICE MONITORING TOOLS =====
    
    # Register add_price_alert
    tool_registry.register(ToolDefinition(
        name="add_price_alert",
        description="Add price alert for validation/invalidation monitoring. Perfect for trade setups - get notified when price validates (confirms) or invalidates (rejects) your trade idea. For LONG: validation_price > current > invalidation_price. For SHORT: validation_price < current < invalidation_price. Choose exchange: drift (default), backpack, or binance.",
        parameters=[
            ToolParameter(
                name="symbol",
                type="string",
                description="Trading symbol (BTC, ETH, SOL, etc.)",
                required=True
            ),
            ToolParameter(
                name="validation_price",
                type="number",
                description="Price level that validates the trade setup (confirms trade is working)",
                required=True
            ),
            ToolParameter(
                name="invalidation_price",
                type="number",
                description="Price level that invalidates the trade setup (stop loss level)",
                required=True
            ),
            ToolParameter(
                name="direction",
                type="string",
                description="Trade direction: LONG (bullish) or SHORT (bearish). Default: LONG",
                required=False
            ),
            ToolParameter(
                name="exchange",
                type="string",
                description="Exchange to monitor: drift (default), backpack, or binance",
                required=False
            )
        ],
        function=add_price_alert
    ))
    
    # Register remove_price_alert
    tool_registry.register(ToolDefinition(
        name="remove_price_alert",
        description="Remove price alert by ID. Use list_price_alerts to get alert IDs.",
        parameters=[
            ToolParameter(
                name="alert_id",
                type="string",
                description="Alert ID to remove",
                required=True
            )
        ],
        function=remove_price_alert
    ))
    
    # Register list_price_alerts
    tool_registry.register(ToolDefinition(
        name="list_price_alerts",
        description="List all price alerts with details. Shows active and triggered alerts, separated by validation/invalidation status. Use to check which trade setups are being monitored.",
        parameters=[
            ToolParameter(
                name="active_only",
                type="boolean",
                description="Only return non-triggered alerts (default: false)",
                required=False
            )
        ],
        function=list_price_alerts
    ))
    
    # Register get_price_alert
    tool_registry.register(ToolDefinition(
        name="get_price_alert",
        description="Get specific price alert details by ID. Shows validation/invalidation prices, current status, and trigger information if already triggered.",
        parameters=[
            ToolParameter(
                name="alert_id",
                type="string",
                description="Alert ID",
                required=True
            )
        ],
        function=get_price_alert
    ))
    
    # Register get_price_monitor_stats
    tool_registry.register(ToolDefinition(
        name="get_price_monitor_stats",
        description="Get price monitor statistics and status. Shows if monitor is running, number of active alerts, total validations/invalidations triggered, and price check count.",
        parameters=[],
        function=get_price_monitor_stats
    ))
    
    # Register start_price_monitor
    tool_registry.register(ToolDefinition(
        name="start_price_monitor",
        description="Start price monitoring. Monitor will poll prices every 10 seconds and alert when validation or invalidation levels are reached. Must be started before alerts will trigger.",
        parameters=[],
        function=start_price_monitor
    ))
    
    # Register stop_price_monitor
    tool_registry.register(ToolDefinition(
        name="stop_price_monitor",
        description="Stop price monitoring. Alerts will not trigger while monitor is stopped.",
        parameters=[],
        function=stop_price_monitor
    ))
    
    # Register TradingView tools
    register_tradingview_tools()
    
    logger.info("Registered 33 trading tools: 9 market/news tools + 7 price monitor tools + 17 TradingView chart tools")
