# TradingView Tools for Rabit Agent

Modular TradingView chart control tools for AI agent integration.

## 📁 Structure

```
tradingview/
├── __init__.py          # Module exports
├── client.py            # HTTP client for chart communication
├── chart.py             # Chart control (symbol, timeframe, type)
├── data.py              # Data reading (quote, OHLCV, indicators)
├── indicators.py        # Indicator management (add, remove, configure)
├── drawing.py           # Drawing tools (lines, levels)
├── alerts.py            # Alert management
└── screenshot.py        # Screenshot capture
```

## 🚀 Setup

### 1. Install Dependencies

```bash
cd Rabit-mobile/assets/charting/advanced-charts
npm install express cors
```

### 2. Start Chart Server (Terminal 1)

```bash
cd Rabit-mobile/assets/charting/advanced-charts
npm start
```

Chart will be available at: http://localhost:3000

### 3. Start API Server (Terminal 2)

```bash
cd Rabit-mobile/assets/charting/advanced-charts
npm run api
```

API server will run at: http://localhost:3001

### 4. Test Tools (Terminal 3)

```bash
cd rabit-backend
python test_tradingview_tools.py
```

## 🎯 Available Tools (17 total)

### Chart Control (5 tools)
- `tv_get_state` - Get current chart state
- `tv_set_symbol` - Change symbol (BTC, ETH, SOL, etc.)
- `tv_set_timeframe` - Change timeframe (1, 5, 15, 60, D, W, M)
- `tv_set_chart_type` - Change chart type (Candles, Line, Area)
- `tv_scroll_to_date` - Jump to specific date

### Data Reading (3 tools)
- `tv_get_quote` - Real-time price data
- `tv_get_ohlcv` - Candlestick data (with summary mode)
- `tv_get_indicator_values` - All indicator values

### Indicators (3 tools)
- `tv_add_indicator` - Add indicator (RSI, MACD, BB, EMA, etc.)
- `tv_remove_indicator` - Remove indicator by ID
- `tv_set_indicator_inputs` - Change indicator settings

### Drawing (3 tools)
- `tv_draw_line` - Draw trend line
- `tv_draw_horizontal_line` - Draw support/resistance level
- `tv_clear_drawings` - Clear all drawings

### Alerts (3 tools)
- `tv_create_alert` - Create price alert
- `tv_list_alerts` - List active alerts
- `tv_delete_alert` - Delete alert

### Screenshot (1 tool)
- `tv_capture_screenshot` - Capture chart image

## 💡 Usage Examples

### In Agent Code

```python
from agents.tools.tradingview import (
    tv_set_symbol,
    tv_set_timeframe,
    tv_get_quote,
    tv_add_indicator,
)

# Change to BTC 1-hour chart
await tv_set_symbol("BTC")
await tv_set_timeframe("60")

# Get current price
quote = await tv_get_quote()
print(f"BTC Price: ${quote['data']['price']}")

# Add RSI indicator
await tv_add_indicator("RSI", {"length": 14})
```

### Via Agent Tools

Tools are automatically registered when `register_tradingview_tools()` is called in `trading_tools.py`.

Agent can use them naturally:
- "Show me BTC on 1 hour chart"
- "Add RSI indicator"
- "What's the current price?"
- "Draw support line at $94000"

## 🔧 Architecture

```
Python Backend (rabit-backend)
    ↓ HTTP POST
API Server (localhost:3001)
    ↓ Command Queue
TradingView Chart (localhost:3000)
    ↓ TradingView Widget API
Chart Display
```

## 📝 Adding New Tools

1. Create function in appropriate file (e.g., `chart.py`)
2. Add to `__init__.py` exports
3. Register in `tradingview_tools.py`
4. Add command handler in `chartApi.js`

## ⚠️ Notes

- Chart must be running at localhost:3000
- API server must be running at localhost:3001
- Commands timeout after 10 seconds
- Some features require TradingView Pro subscription
- Tools use dummy data for now - implement real data fetching in chartApi.js

## 🐛 Troubleshooting

**Cannot connect to chart:**
- Make sure chart is running: `npm start`
- Check http://localhost:3000 in browser

**Cannot connect to API:**
- Make sure API server is running: `npm run api`
- Check http://localhost:3001/health

**Commands timeout:**
- Chart may be loading - wait a few seconds
- Check browser console for errors
- Restart both servers

## 📚 References

- TradingView Widget API: https://www.tradingview.com/widget-docs/
- Based on: tradingview-mcp-jackson (MCP implementation)
