# TradingView Tools Setup Guide

## 📋 Overview

TradingView tools telah diimplementasikan untuk Rabit Agent dengan 17 tools yang memungkinkan kontrol penuh terhadap TradingView chart.

## 🎯 Tools yang Tersedia

### 1. Chart Control (5 tools)
- ✅ `tv_get_state` - Get symbol, timeframe, chart type, indicators
- ✅ `tv_set_symbol` - Ganti symbol (BTC, ETH, SOL, dll)
- ✅ `tv_set_timeframe` - Ganti timeframe (1m, 5m, 1h, 1d, dll)
- ✅ `tv_set_chart_type` - Ganti chart type (Candles, Line, Area)
- ✅ `tv_scroll_to_date` - Jump ke tanggal tertentu

### 2. Data Reading (3 tools)
- ✅ `tv_get_quote` - Real-time price, OHLC, volume
- ✅ `tv_get_ohlcv` - Candlestick data dengan summary mode
- ✅ `tv_get_indicator_values` - Nilai semua indicator

### 3. Indicator Management (3 tools)
- ✅ `tv_add_indicator` - Add RSI, MACD, BB, EMA, dll
- ✅ `tv_remove_indicator` - Remove indicator by ID
- ✅ `tv_set_indicator_inputs` - Change indicator settings

### 4. Drawing Tools (3 tools)
- ✅ `tv_draw_line` - Draw trend line
- ✅ `tv_draw_horizontal_line` - Draw support/resistance
- ✅ `tv_clear_drawings` - Clear all drawings

### 5. Alerts (3 tools)
- ✅ `tv_create_alert` - Create price alert
- ✅ `tv_list_alerts` - List active alerts
- ✅ `tv_delete_alert` - Delete alert

### 6. Screenshot (1 tool)
- ✅ `tv_capture_screenshot` - Capture chart image

## 🚀 Quick Start

### Step 1: Start Chart Server

```bash
# Terminal 1
cd Rabit-mobile/assets/charting/advanced-charts
npm start
```

Chart akan berjalan di: **http://localhost:3000**

### Step 2: Start API Server

```bash
# Terminal 2
cd Rabit-mobile/assets/charting/advanced-charts
npm run api
```

API server akan berjalan di: **http://localhost:3001**

### Step 3: Test Tools

```bash
# Terminal 3
cd rabit-backend
python test_tradingview_tools.py
```

## 📁 Struktur File

```
rabit-backend/
├── agents/
│   ├── tools/
│   │   ├── tradingview/              # TradingView tools module
│   │   │   ├── __init__.py           # Exports
│   │   │   ├── client.py             # HTTP client
│   │   │   ├── chart.py              # Chart control
│   │   │   ├── data.py               # Data reading
│   │   │   ├── indicators.py         # Indicator management
│   │   │   ├── drawing.py            # Drawing tools
│   │   │   ├── alerts.py             # Alert management
│   │   │   ├── screenshot.py         # Screenshot
│   │   │   └── README.md             # Documentation
│   │   └── tradingview_tools.py      # Tool registration
│   └── examples/
│       └── trading_tools.py          # Updated with TV tools
└── test_tradingview_tools.py         # Test script

Rabit-mobile/
└── assets/
    └── charting/
        └── advanced-charts/
            ├── src/
            │   ├── api/
            │   │   └── chartApi.js   # Chart API handler
            │   ├── server/
            │   │   └── api.js        # Express API server
            │   └── advanced_chart.js # Updated with API
            ├── package.json          # Updated with scripts
            └── start-api.bat         # API server launcher
```

## 💡 Usage Examples

### Example 1: Analyze BTC Chart

```python
# Agent receives: "Analyze BTC on 1 hour chart"

# Agent will execute:
await tv_set_symbol("BTC")
await tv_set_timeframe("60")
await tv_get_quote()
await tv_get_indicator_values()
await tv_capture_screenshot()
```

### Example 2: Add Indicators

```python
# Agent receives: "Add RSI and MACD indicators"

# Agent will execute:
await tv_add_indicator("RSI", {"length": 14})
await tv_add_indicator("MACD", {"fast": 12, "slow": 26, "signal": 9})
```

### Example 3: Draw Support Level

```python
# Agent receives: "Draw support line at $94000"

# Agent will execute:
await tv_draw_horizontal_line(
    price=94000,
    color="#FD4C01",
    text="Support Level"
)
```

### Example 4: Set Price Alert

```python
# Agent receives: "Alert me when BTC crosses $95000"

# Agent will execute:
await tv_create_alert(
    condition="crossing",
    price=95000,
    message="BTC crossed $95000"
)
```

## 🔧 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Rabit Agent (Python)                  │
│  ┌────────────────────────────────────────────────────┐ │
│  │         TradingView Tools (17 tools)               │ │
│  │  - Chart Control  - Data Reading                   │ │
│  │  - Indicators     - Drawing                        │ │
│  │  - Alerts         - Screenshot                     │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↓ HTTP POST
┌─────────────────────────────────────────────────────────┐
│            API Server (localhost:3001)                   │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Express.js Server                                 │ │
│  │  - Command Queue                                   │ │
│  │  - Response Queue                                  │ │
│  │  - Timeout Handling                                │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↓ Command Polling
┌─────────────────────────────────────────────────────────┐
│         TradingView Chart (localhost:3000)               │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Chart API Handler (chartApi.js)                   │ │
│  │  - Command Execution                               │ │
│  │  - TradingView Widget API                          │ │
│  │  - Response Sending                                │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 🧪 Testing

### Manual Test

```bash
cd rabit-backend
python test_tradingview_tools.py
```

Test akan:
1. ✅ Check connection ke chart
2. ✅ Test chart control (symbol, timeframe)
3. ✅ Test data reading (quote, OHLCV)
4. ✅ Test indicators (add RSI)
5. ✅ Test drawing (horizontal line)

### Test via Agent

```python
from agents.core import TradingAgent
from agents.examples.trading_tools import register_trading_tools

# Register tools
register_trading_tools()

# Create agent
agent = TradingAgent(scope_id="test_user")

# Test query
response = await agent.process_trading_query(
    "Show me BTC on 1 hour chart and add RSI indicator"
)
```

## 📝 Next Steps

### Phase 1: Complete Implementation ✅
- [x] Create modular tool structure
- [x] Implement HTTP client
- [x] Implement 17 tools
- [x] Create API server
- [x] Register tools
- [x] Create test script

### Phase 2: Chart Integration (TODO)
- [ ] Implement real data fetching in chartApi.js
- [ ] Add command polling in advanced_chart.js
- [ ] Test with live chart
- [ ] Handle edge cases

### Phase 3: Advanced Features (TODO)
- [ ] Pine Script tools
- [ ] Multi-pane layouts
- [ ] Replay mode
- [ ] Batch operations

## ⚠️ Important Notes

1. **Chart must be running** at localhost:3000
2. **API server must be running** at localhost:3001
3. **Commands timeout** after 10 seconds
4. **Some features** require TradingView Pro subscription
5. **Currently using dummy data** - implement real data in chartApi.js

## 🐛 Troubleshooting

### Cannot connect to chart
```bash
# Check if chart is running
curl http://localhost:3000

# Start chart if not running
cd Rabit-mobile/assets/charting/advanced-charts
npm start
```

### Cannot connect to API
```bash
# Check if API is running
curl http://localhost:3001/health

# Start API if not running
cd Rabit-mobile/assets/charting/advanced-charts
npm run api
```

### Commands timeout
- Chart may be loading - wait a few seconds
- Check browser console for errors
- Restart both servers

### Tools not registered
```python
# Make sure tools are registered
from agents.examples.trading_tools import register_trading_tools
register_trading_tools()
```

## 📚 References

- TradingView Widget API: https://www.tradingview.com/widget-docs/
- TradingView MCP Jackson: https://github.com/LewisWJackson/tradingview-mcp-jackson
- Rabit Agent Documentation: `rabit-backend/docs/agents/`

---

**Status**: ✅ Implementation Complete - Ready for Testing
**Date**: 2026-04-16
**Version**: 1.0.0
