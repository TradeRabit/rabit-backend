# TradingView Chart State Management - Implementation Summary

## 🎯 Problem Solved

**Original Issue:**
- Chart harus dibuka dulu di assist page baru TradingView load
- Agent tidak bisa control chart jika user belum buka assist page
- User kehilangan chart configuration (symbol, timeframe, indicators) saat navigate away

**Solution:**
- ✅ Chart selalu pre-loaded di background (minimized by default)
- ✅ State management dengan localStorage untuk persistent configuration
- ✅ Auto-restore symbol, timeframe, indicators, drawings
- ✅ Agent bisa langsung control chart tanpa user harus buka dulu

## 📦 Files Created/Modified

### New Files:
1. **`Rabit-mobile/assets/charting/advanced-charts/src/utils/chartStateManager.js`**
   - Singleton state manager
   - Save/load state to localStorage
   - Track symbol, timeframe, chart type, indicators, drawings
   - State freshness check (24 hours)

2. **`Rabit-mobile/assets/charting/advanced-charts/STATE_MANAGEMENT.md`**
   - Documentation for state management
   - Usage examples
   - Debugging guide

3. **`rabit-backend/TRADINGVIEW_STATE_MANAGEMENT.md`**
   - Implementation summary
   - Architecture overview

### Modified Files:
1. **`Rabit-mobile/assets/charting/advanced-charts/src/advanced_chart.js`**
   - Import chartStateManager
   - Load saved state on initialization
   - Auto-restore symbol, timeframe, chart type
   - Auto-restore indicators (if state fresh)
   - Update state on command execution
   - Integrate state manager with command polling

2. **`Rabit-mobile/app/assist.tsx`**
   - Change default chartState to 'minimized' (was 'closed')
   - Chart always rendered (even when minimized)
   - Use opacity: 0 and height: 0 instead of display: none
   - Chart WebView loads immediately on page mount
   - Add console log when chart ready

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Assist Page (React Native)            │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Chart Component (Always Rendered)                 │ │
│  │  - State: minimized (default)                      │ │
│  │  - WebView: Always loaded                          │ │
│  │  - Visibility: Hidden when minimized               │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│         TradingView Chart (localhost:3000)               │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Chart State Manager                               │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │  localStorage: tradingview_chart_state       │ │ │
│  │  │  {                                            │ │ │
│  │  │    symbol: 'BTCUSDT',                        │ │ │
│  │  │    timeframe: '60',                          │ │ │
│  │  │    chartType: 1,                             │ │ │
│  │  │    indicators: [...],                        │ │ │
│  │  │    drawings: [...],                          │ │ │
│  │  │    lastUpdated: 1776331528181                │ │ │
│  │  │  }                                            │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  On Load:                                                │
│  1. Load state from localStorage                         │
│  2. Apply saved symbol & timeframe                       │
│  3. Restore chart type                                   │
│  4. Restore indicators (if fresh)                        │
│  5. Start command polling                                │
│                                                          │
│  On Command:                                             │
│  1. Execute command                                      │
│  2. Update state manager                                 │
│  3. Save to localStorage                                 │
│  4. Return result                                        │
└─────────────────────────────────────────────────────────┘
                          ↑
                    Agent Commands
```

## 🔄 State Lifecycle

### 1. Initial Load
```javascript
// Chart loads
const stateManager = getChartStateManager();
const savedState = stateManager.getState();

// Apply saved state
widget.setSymbol(savedState.symbol);
widget.setResolution(savedState.timeframe);
widget.setChartType(savedState.chartType);

// Restore indicators (if fresh)
if (stateManager.isStateFresh()) {
  savedState.indicators.forEach(indicator => {
    widget.createStudy(indicator.name, false, false, indicator.inputs);
  });
}
```

### 2. Command Execution
```javascript
// Agent sends command
const result = await chartAPI.handleCommand('SET_SYMBOL', { symbol: 'BTC' });

// Update state
if (result.success) {
  stateManager.setSymbol('BTC');
  // Automatically saved to localStorage
}
```

### 3. State Persistence
```javascript
// State is saved to localStorage
localStorage.setItem('tradingview_chart_state', JSON.stringify({
  symbol: 'BTC',
  timeframe: '60',
  chartType: 1,
  indicators: [...],
  drawings: [...],
  lastUpdated: Date.now()
}));
```

## 💡 Key Features

### 1. Pre-loading Strategy
- Chart is **always rendered** when assist page mounts
- Default state: **minimized** (not closed)
- WebView loads immediately in background
- User sees minimized header bar
- Agent can send commands immediately

### 2. State Persistence
- All chart configuration saved to localStorage
- Survives page refresh and app restart
- State includes: symbol, timeframe, chart type, indicators, drawings
- Automatic save on every state change

### 3. State Freshness
- Indicators only restored if state < 24 hours old
- Prevents stale configurations
- Symbol and timeframe always restored
- Configurable freshness threshold

### 4. Seamless Integration
- State updates automatically on agent commands
- No manual state management needed
- Works with all 17 TradingView tools
- Transparent to agent - just send commands

## 🧪 Testing

### Test Pre-loading
1. Open assist page
2. Chart should be minimized by default
3. Check console: "Chart is ready and can receive commands"
4. Send agent command (even with chart minimized)
5. Command should execute successfully

### Test State Persistence
1. Change symbol to BTC: `await tv_set_symbol("BTC")`
2. Change timeframe to 1h: `await tv_set_timeframe("60")`
3. Add RSI: `await tv_add_indicator("RSI")`
4. Refresh page
5. Chart should restore to BTC, 1h, with RSI

### Test State Freshness
1. Set state with indicators
2. Wait 25 hours (or manually change lastUpdated)
3. Refresh page
4. Symbol and timeframe restored
5. Indicators NOT restored (state too old)

## 📊 State Manager API

```javascript
import { getChartStateManager } from './utils/chartStateManager';

const stateManager = getChartStateManager();

// Get state
const state = stateManager.getState();

// Update state
stateManager.setSymbol('ETHUSDT');
stateManager.setTimeframe('15');
stateManager.setChartType(2); // Line chart

// Indicators
stateManager.addIndicator({
  name: 'RSI',
  entity_id: 'abc123',
  inputs: { length: 14 }
});
stateManager.removeIndicator('abc123');

// Drawings
stateManager.addDrawing({
  id: 'line_123',
  type: 'horizontal_line',
  params: { price: 95000 }
});
stateManager.clearDrawings();

// Utility
stateManager.isStateFresh(); // Check if < 24 hours old
stateManager.clearState();   // Reset to default
```

## 🎨 User Experience

### Before:
1. User opens assist page → Chart closed
2. User asks agent to analyze BTC
3. Agent sends command → **FAILS** (chart not loaded)
4. User must manually open chart first
5. Agent sends command again → Success

### After:
1. User opens assist page → Chart minimized (pre-loaded)
2. User asks agent to analyze BTC
3. Agent sends command → **SUCCESS** (chart ready)
4. Chart updates in background
5. User can expand chart to see results

## 🚀 Benefits

1. **Instant Agent Control**
   - No waiting for chart to load
   - Commands execute immediately
   - Better user experience

2. **Persistent Configuration**
   - User preferences saved
   - No need to reconfigure chart
   - Seamless across sessions

3. **Background Operation**
   - Chart works even when minimized
   - Agent can prepare analysis before user opens chart
   - Efficient resource usage

4. **Automatic State Management**
   - No manual save/load needed
   - State updates on every command
   - Transparent to developer

## 🔧 Configuration

### Adjust State Freshness
```javascript
// In chartStateManager.js
isStateFresh() {
  const age = Date.now() - this.state.lastUpdated;
  const maxAge = 48 * 60 * 60 * 1000; // Change to 48 hours
  return age < maxAge;
}
```

### Change Default State
```javascript
// In chartStateManager.js
loadState() {
  // ...
  return {
    symbol: 'ETHUSDT',  // Change default symbol
    timeframe: '15',    // Change default timeframe
    chartType: 2,       // Change to line chart
    indicators: [],
    drawings: [],
    lastUpdated: Date.now(),
  };
}
```

### Disable Auto-restore
```javascript
// In advanced_chart.js
// Comment out indicator restoration
/*
if (savedState.indicators && savedState.indicators.length > 0) {
  // ...
}
*/
```

## 📝 Future Enhancements

- [ ] Sync state with backend database (multi-device)
- [ ] User-specific state (per user ID)
- [ ] Multiple chart presets
- [ ] Export/import configurations
- [ ] State versioning for migrations
- [ ] Undo/redo state changes
- [ ] State compression for large configs

---

**Status**: ✅ Implemented and Tested
**Date**: 2026-04-16
**Version**: 1.0.0
