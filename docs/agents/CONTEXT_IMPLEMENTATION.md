# Trading Context Implementation

## Overview

Created a context management system for the trading agent to track:
- **Current Exchange**: drift or backpack
- **Current Asset**: BTC, ETH, SOL, etc.
- **Trading Mode**: asset-locked or global

## Files Created

### 1. `agents/context/trading_context.py`
Core implementation with:
- `TradingContext` dataclass
- Context management functions (get, set, update, clear)
- Context formatting for agent prompts

### 2. `agents/context/__init__.py`
Clean exports for:
- `get_trading_context()`
- `set_trading_context()`
- `update_exchange()`
- `update_asset()`
- `update_mode()`
- `get_context_for_agent()`

### 3. `agents/context/README.md`
Comprehensive documentation covering:
- Trading modes (global vs asset-locked)
- Exchange selection (drift vs backpack)
- Usage examples
- API reference
- Integration points

### 4. `test/context/test_trading_context.py`
Complete test suite with:
- Unit tests for all functions
- Real-world scenario tests
- Edge case handling

## Key Features

### Exchange Management
```python
# Only 2 exchanges supported
set_trading_context(exchange="drift")  # Default
set_trading_context(exchange="backpack")  # Alternative

# Binance is only for historical OHLC, not live trading
```

### Trading Modes

#### Global Mode (Assist Page)
```python
# User can trade any asset
set_trading_context(
    exchange="drift",
    mode="global"
)
```

#### Asset-Locked Mode (Asset Detail Page)
```python
# User locked to specific asset (e.g., BTC detail page → "Trade Now")
set_trading_context(
    exchange="drift",
    asset="BTC",
    mode="asset_locked"
)
```

### Context for Agent
```python
# Get formatted context string for agent system prompt
context_str = get_context_for_agent()

# Output:
# === CURRENT TRADING CONTEXT ===
# Exchange: DRIFT
# Mode: Asset Locked
# Asset: BTC
# Last Updated: 2026-04-16 10:30:45
# ===============================
```

## Integration Points

### Frontend (React Native)

#### Home Page Header
- **Location**: `Rabit-mobile/components/organisms/AppHeader/AppHeader.tsx`
- **Feature**: Exchange dropdown (Drift logo + chevron)
- **Action**: User switches between drift and backpack
- **Backend Call**: Update context via API

```typescript
// When user switches exchange
fetch('/api/agent/context', {
  method: 'POST',
  body: JSON.stringify({ exchange: 'backpack' })
})
```

#### Assist Page (Global Mode)
- **Location**: `Rabit-mobile/app/assist.tsx`
- **Feature**: Chat with agent, can trade any asset
- **Context**: `mode=global, asset=None`

```typescript
// When navigating to assist from home
fetch('/api/agent/context', {
  method: 'POST',
  body: JSON.stringify({ 
    exchange: currentExchange,
    mode: 'global'
  })
})
```

#### Asset Detail Page (Asset-Locked Mode)
- **Location**: `Rabit-mobile/app/asset-detail/[id].tsx`
- **Feature**: "Trade Now" button locks to specific asset
- **Context**: `mode=asset_locked, asset=BTC`

```typescript
// When user clicks "Trade Now" on BTC detail page
fetch('/api/agent/context', {
  method: 'POST',
  body: JSON.stringify({ 
    exchange: currentExchange,
    asset: 'BTC',
    mode: 'asset_locked'
  })
})
```

### Backend API (To Be Created)

```python
# api/routes.py

from agents import set_trading_context, get_trading_context

@app.post("/api/agent/context")
async def update_agent_context(request: ContextRequest):
    """Update trading context"""
    context = set_trading_context(
        exchange=request.exchange,
        asset=request.asset,
        mode=request.mode
    )
    return {"success": True, "context": context.to_dict()}

@app.get("/api/agent/context")
async def get_agent_context():
    """Get current trading context"""
    context = get_trading_context()
    if context:
        return {"context": context.to_dict()}
    return {"context": None}
```

### Agent System Prompt

```python
from agents import get_trading_agent_prompt, get_context_for_agent

# Load base prompt
base_prompt = get_trading_agent_prompt()

# Add context
context = get_context_for_agent()
full_prompt = f"{base_prompt}\n\n{context}"

# Use in agent
agent = TradingAgent(system_prompt=full_prompt)
```

## Usage Examples

### Example 1: User on Home Page
```python
# User selects Drift exchange
set_trading_context(exchange="drift", mode="global")

# Agent can trade any asset
context = get_trading_context()
print(context.get_context_summary())
# Output: "Trading on DRIFT (Global Mode - All Assets)"
```

### Example 2: User on BTC Detail Page
```python
# User clicks "Trade Now" on BTC detail page
set_trading_context(
    exchange="drift",
    asset="BTC",
    mode="asset_locked"
)

# Agent is locked to BTC
context = get_trading_context()
print(context.get_context_summary())
# Output: "Trading BTC on DRIFT (Asset-Locked Mode)"
```

### Example 3: User Switches Exchange
```python
# User switches from Drift to Backpack
update_exchange("backpack")

# Context preserved, only exchange changes
context = get_trading_context()
print(f"Now trading on {context.exchange}")
# Output: "Now trading on backpack"
```

## Mobile App Flow

### Flow 1: Home → Assist (Global)
1. User on home page
2. User selects exchange via dropdown (drift/backpack)
3. User navigates to Assist page
4. **Backend**: `set_trading_context(exchange=selected, mode="global")`
5. Agent can trade any asset

### Flow 2: Asset Detail → Assist (Locked)
1. User views asset detail page (`/asset-detail/BTC`)
2. User clicks "Trade Now" button
3. Navigates to Assist page
4. **Backend**: `set_trading_context(exchange=current, asset="BTC", mode="asset_locked")`
5. Agent only trades BTC

### Flow 3: Exchange Switch
1. User clicks exchange dropdown in header
2. Selects different exchange (drift ↔ backpack)
3. **Backend**: `update_exchange(new_exchange)`
4. All subsequent trades use new exchange

## Testing

Run tests:
```bash
pytest test/context/test_trading_context.py -v
```

Test coverage:
- ✅ Context creation and management
- ✅ Exchange updates
- ✅ Asset updates
- ✅ Mode switching
- ✅ Error handling
- ✅ Real-world scenarios

## Next Steps

### 1. Create API Endpoints
- `POST /api/agent/context` - Update context
- `GET /api/agent/context` - Get current context

### 2. Frontend Integration
- Add API calls in AppHeader for exchange switching
- Add API call in assist.tsx on page load
- Add API call in asset-detail/[id].tsx on "Trade Now"

### 3. Agent Integration
- Inject context into agent system prompt
- Update agent to respect context constraints
- Add context validation in tool calls

### 4. Add Backpack Logo
- Add Backpack logo assets to `Rabit-mobile/assets/Dex/Backpack/`
- Update `constants/theme.ts` to include Backpack logos
- Update AppHeader to show Backpack logo when selected

## Notes

- Context is stored in-memory (singleton pattern)
- Context persists across agent calls within same session
- Context is cleared when backend restarts
- For production, consider persisting in database or Redis
- Asset symbols are automatically normalized to uppercase
- Exchange names are case-insensitive but stored as lowercase

## Summary

✅ Created complete context management system
✅ Supports 2 exchanges (drift, backpack)
✅ Supports 2 modes (global, asset-locked)
✅ Clean API with comprehensive documentation
✅ Full test coverage
✅ Ready for frontend integration
