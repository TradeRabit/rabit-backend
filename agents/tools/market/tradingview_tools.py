"""TradingView tools registration"""
from agents.tools import tool_registry, ToolDefinition, ToolParameter
from agents.tools.tradingview import (
    # Chart control
    tv_get_state,
    tv_set_symbol,
    tv_set_timeframe,
    tv_set_chart_type,
    tv_scroll_to_date,
    # Data reading
    tv_get_quote,
    tv_get_ohlcv,
    tv_get_indicator_values,
    # Indicators
    tv_add_indicator,
    tv_remove_indicator,
    tv_set_indicator_inputs,
    # Drawing
    tv_draw_line,
    tv_draw_horizontal_line,
    tv_clear_drawings,
    # Alerts
    tv_create_alert,
    tv_list_alerts,
    tv_delete_alert,
    # Screenshot
    tv_capture_screenshot,
)
from utils.logger import get_logger

logger = get_logger(__name__)


def register_tradingview_tools():
    """Register TradingView tools to the registry"""
    
    # ===== CHART CONTROL =====
    
    tool_registry.register(ToolDefinition(
        name="tv_get_state",
        description="Get current TradingView chart state including symbol, timeframe, chart type, and list of all indicators with their IDs. Call this first to understand what's on the chart.",
        parameters=[],
        function=tv_get_state
    ))
    
    tool_registry.register(ToolDefinition(
        name="tv_set_symbol",
        description="Change the chart symbol/ticker. Use uppercase symbols like BTC, ETH, SOL, DOGE, etc.",
        parameters=[
            ToolParameter(
                name="symbol",
                type="string",
                description="Trading symbol in uppercase (e.g., BTC, ETH, SOL, DOGE, BNB)",
                required=True
            )
        ],
        function=tv_set_symbol
    ))
    
    tool_registry.register(ToolDefinition(
        name="tv_set_timeframe",
        description="Change the chart timeframe/resolution. Valid options: 1 (1min), 5 (5min), 15 (15min), 30 (30min), 60 (1hour), 240 (4hour), D (daily), W (weekly), M (monthly).",
        parameters=[
            ToolParameter(
                name="timeframe",
                type="string",
                description="Timeframe: 1, 5, 15, 30, 60, 240, D, W, M",
                required=True
            )
        ],
        function=tv_set_timeframe
    ))
    
    tool_registry.register(ToolDefinition(
        name="tv_set_chart_type",
        description="Change the chart visualization type. Options: Candles (default), Line, Area, HeikinAshi, Bars.",
        parameters=[
            ToolParameter(
                name="chart_type",
                type="string",
                description="Chart type: Candles, Line, Area, HeikinAshi, Bars",
                required=True
            )
        ],
        function=tv_set_chart_type
    ))
    
    tool_registry.register(ToolDefinition(
        name="tv_scroll_to_date",
        description="Scroll the chart to center on a specific date. Useful for historical analysis.",
        parameters=[
            ToolParameter(
                name="date",
                type="string",
                description="ISO date string (e.g., '2024-01-15')",
                required=True
            )
        ],
        function=tv_scroll_to_date
    ))
    
    # ===== DATA READING =====
    
    tool_registry.register(ToolDefinition(
        name="tv_get_quote",
        description="Get real-time quote data for current or specified symbol. Returns price, OHLC, volume, and market data.",
        parameters=[
            ToolParameter(
                name="symbol",
                type="string",
                description="Optional symbol to quote (uses current chart symbol if not provided)",
                required=False
            )
        ],
        function=tv_get_quote
    ))
    
    tool_registry.register(ToolDefinition(
        name="tv_get_ohlcv",
        description="Get OHLCV candlestick data. Use summary=true for compact stats (high, low, range, change%) instead of all bars to save context. Max 500 bars.",
        parameters=[
            ToolParameter(
                name="count",
                type="number",
                description="Number of bars to retrieve (default: 100, max: 500)",
                required=False
            ),
            ToolParameter(
                name="summary",
                type="boolean",
                description="Return summary stats instead of all bars (default: true, recommended)",
                required=False
            )
        ],
        function=tv_get_ohlcv
    ))
    
    tool_registry.register(ToolDefinition(
        name="tv_get_indicator_values",
        description="Get current values from ALL visible indicators on the chart (RSI, MACD, Bollinger Bands, EMAs, custom indicators). Returns numeric values for each indicator.",
        parameters=[],
        function=tv_get_indicator_values
    ))
    
    # ===== INDICATORS =====
    
    tool_registry.register(ToolDefinition(
        name="tv_add_indicator",
        description="Add technical indicator to chart. Supports common indicators: RSI, MACD, BB (Bollinger Bands), EMA, SMA, Volume, Stochastic, ATR, ADX. Can also use full names like 'Relative Strength Index'.",
        parameters=[
            ToolParameter(
                name="indicator",
                type="string",
                description="Indicator name (short: RSI, MACD, BB, EMA, SMA or full: 'Relative Strength Index')",
                required=True
            ),
            ToolParameter(
                name="inputs",
                type="object",
                description="Optional input overrides (e.g., {\"length\": 20, \"source\": \"close\"})",
                required=False
            )
        ],
        function=tv_add_indicator
    ))
    
    tool_registry.register(ToolDefinition(
        name="tv_remove_indicator",
        description="Remove indicator from chart by entity ID. Get entity IDs from tv_get_state.",
        parameters=[
            ToolParameter(
                name="entity_id",
                type="string",
                description="Entity ID of indicator to remove (from tv_get_state)",
                required=True
            )
        ],
        function=tv_remove_indicator
    ))
    
    tool_registry.register(ToolDefinition(
        name="tv_set_indicator_inputs",
        description="Change indicator settings/inputs (e.g., change RSI length from 14 to 20). Get entity ID from tv_get_state.",
        parameters=[
            ToolParameter(
                name="entity_id",
                type="string",
                description="Entity ID of indicator (from tv_get_state)",
                required=True
            ),
            ToolParameter(
                name="inputs",
                type="object",
                description="Input overrides (e.g., {\"length\": 50, \"source\": \"close\"})",
                required=True
            )
        ],
        function=tv_set_indicator_inputs
    ))
    
    # ===== DRAWING =====
    
    tool_registry.register(ToolDefinition(
        name="tv_draw_line",
        description="Draw trend line on chart between two points (price and time coordinates).",
        parameters=[
            ToolParameter(
                name="price1",
                type="number",
                description="Start price",
                required=True
            ),
            ToolParameter(
                name="time1",
                type="string",
                description="Start time (ISO format)",
                required=True
            ),
            ToolParameter(
                name="price2",
                type="number",
                description="End price",
                required=True
            ),
            ToolParameter(
                name="time2",
                type="string",
                description="End time (ISO format)",
                required=True
            ),
            ToolParameter(
                name="color",
                type="string",
                description="Line color (hex, default: #FD4C01)",
                required=False
            ),
            ToolParameter(
                name="width",
                type="number",
                description="Line width (default: 2)",
                required=False
            )
        ],
        function=tv_draw_line
    ))
    
    tool_registry.register(ToolDefinition(
        name="tv_draw_horizontal_line",
        description="Draw horizontal line at specific price level. Useful for support/resistance levels, entry/exit points.",
        parameters=[
            ToolParameter(
                name="price",
                type="number",
                description="Price level for horizontal line",
                required=True
            ),
            ToolParameter(
                name="color",
                type="string",
                description="Line color (hex, default: #FD4C01)",
                required=False
            ),
            ToolParameter(
                name="width",
                type="number",
                description="Line width (default: 2)",
                required=False
            ),
            ToolParameter(
                name="text",
                type="string",
                description="Optional label text (e.g., 'Support', 'Resistance')",
                required=False
            )
        ],
        function=tv_draw_horizontal_line
    ))
    
    tool_registry.register(ToolDefinition(
        name="tv_clear_drawings",
        description="Clear all drawings (lines, shapes, text) from the chart.",
        parameters=[],
        function=tv_clear_drawings
    ))
    
    # ===== ALERTS =====
    
    tool_registry.register(ToolDefinition(
        name="tv_create_alert",
        description="Create price alert. Conditions: crossing (price crosses level), greater_than (price above level), less_than (price below level).",
        parameters=[
            ToolParameter(
                name="condition",
                type="string",
                description="Alert condition: crossing, greater_than, less_than",
                required=True
            ),
            ToolParameter(
                name="price",
                type="number",
                description="Price level for alert",
                required=True
            ),
            ToolParameter(
                name="message",
                type="string",
                description="Alert message (optional)",
                required=False
            )
        ],
        function=tv_create_alert
    ))
    
    tool_registry.register(ToolDefinition(
        name="tv_list_alerts",
        description="List all active price alerts on the chart.",
        parameters=[],
        function=tv_list_alerts
    ))
    
    tool_registry.register(ToolDefinition(
        name="tv_delete_alert",
        description="Delete alert by ID. Get alert IDs from tv_list_alerts.",
        parameters=[
            ToolParameter(
                name="alert_id",
                type="string",
                description="Alert ID to delete (from tv_list_alerts)",
                required=True
            )
        ],
        function=tv_delete_alert
    ))
    
    # ===== SCREENSHOT =====
    
    tool_registry.register(ToolDefinition(
        name="tv_capture_screenshot",
        description="Capture screenshot of the chart. Regions: full (entire window), chart (chart area only), indicators (indicators panel).",
        parameters=[
            ToolParameter(
                name="region",
                type="string",
                description="Screenshot region: full, chart, indicators (default: chart)",
                required=False
            )
        ],
        function=tv_capture_screenshot
    ))
    
    logger.info("Registered 17 TradingView tools: chart control (5), data reading (3), indicators (3), drawing (3), alerts (3), screenshot (1)")
