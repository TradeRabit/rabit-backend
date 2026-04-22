# Agent Context Module

This module manages the trading context for AI agents, providing information about:
- **Current Exchange**: phantom, spot, or futures
- **Current Asset**: BTC, ETH, SOL, etc.
- **Trading Mode**: asset-locked or global

## Trading Modes

### 1. Global Mode
- Agent can trade **any asset** available on the exchange
- Used in the **Assist page** (`/assist`)
- User can switch between different assets freely
- Example: User asks "What's the price of BTC?" then "Show me ETH chart"

### 2. Asset-Locked Mode
- Agent is **locked to a specific asset**
- Used in the **Asset Detail page** (`/asset-detail/[id]`)
- When user clicks "Trade Now" button on an asset detail page
- Example: User is on BTC detail page → clicks "Trade Now" → agent only trades BTC

## Exchange Selection

The app supports 3 exchange modes:
- **Phantom**: Default app-facing venue
- **Spot**: Spot-market mode
- **Futures**: Futures-market mode

Users can switch exchanges via the dropdown in the home page header (logo + chevron icon).

**Note**: Historical OHLC and live market data now come from the Phantom/Hyperliquid market layer.

## Usage

### Setting Context

```python
from agents.context import set_trading_context

# Set full context (asset-locked mode)
context = set_trading_context(
    exchange="phantom",
    asset="BTC",
    mode="asset_locked"
)

# Set global mode
context = set_trading_context(
    exchange="spot",
    mode="global"
)
```

### Updating Context

```python
from agents.context import update_exchange, update_asset, update_mode

# Switch exchange
update_exchange("spot")

# Change asset
update_asset("ETH")

# Switch to global mode
update_mode("global")
```

### Getting Context

```python
from agents.context import get_trading_context, get_context_for_agent

# Get context object
context = get_trading_context()
if context:
    print(f"Trading {context.asset} on {context.exchange}")

# Get formatted string for agent prompt
context_str = get_context_for_agent()
print(context_str)
# Output:
# === CURRENT TRADING CONTEXT ===
# Exchange: PHANTOM
# Mode: Asset Locked
# Asset: BTC
# Last Updated: 2026-04-16 10:30:45
# ===============================
```

### Integration with Agent

```python
from agents.context import get_context_for_agent
from agents.system_prompts import load_trading_agent_prompt

# Get base system prompt
base_prompt = load_trading_agent_prompt()

# Add context to prompt
context = get_context_for_agent()
full_prompt = f"{base_prompt}\n\n{context}"

# Use in agent initialization
agent = TradingAgent(system_prompt=full_prompt)
```

## Context Flow

### Home Page → Assist (Global Mode)
1. User is on home page
2. User selects exchange via dropdown (phantom/spot/futures)
3. User navigates to Assist page
4. Context: `exchange=selected, mode=global, asset=None`
5. Agent can trade any asset

### Asset Detail → Assist (Asset-Locked Mode)
1. User views asset detail page (e.g., `/asset-detail/BTC`)
2. User clicks "Trade Now" button
3. Navigates to Assist page
4. Context: `exchange=current, mode=asset_locked, asset=BTC`
5. Agent only trades BTC

### Switching Exchange
1. User clicks exchange dropdown in header
2. Selects different exchange (phantom ↔ spot/futures)
3. Context updates: `exchange=new_exchange`
4. All subsequent trades use new exchange

## API Reference

### `TradingContext`
Dataclass representing trading context.

**Attributes:**
- `exchange: ExchangeType` - Current exchange (phantom, spot, or futures)
- `asset: Optional[str]` - Current asset symbol (e.g., BTC, ETH)
- `mode: TradingMode` - Trading mode (asset_locked or global)
- `updated_at: Optional[datetime]` - Last update timestamp

### `get_trading_context() -> Optional[TradingContext]`
Get current trading context.

### `set_trading_context(exchange, asset=None, mode="global") -> TradingContext`
Set complete trading context.

**Args:**
- `exchange: ExchangeType` - Exchange to use (phantom, spot, or futures)
- `asset: Optional[str]` - Asset symbol (required for asset_locked mode)
- `mode: TradingMode` - Trading mode (default: global)

**Raises:**
- `ValueError` - If asset is None in asset_locked mode

### `update_exchange(exchange) -> TradingContext`
Update only the exchange in current context.

### `update_asset(asset) -> TradingContext`
Update only the asset in current context.

### `update_mode(mode) -> TradingContext`
Update only the trading mode.

**Raises:**
- `ValueError` - If switching to asset_locked without asset

### `clear_trading_context()`
Clear current trading context.

### `get_context_for_agent() -> str`
Get formatted context string for agent system prompt.

## Examples

### Example 1: User on Home Page
```python
# User selects Phantom exchange
set_trading_context(exchange="phantom", mode="global")

# Agent can now trade any asset in Phantom mode
context = get_trading_context()
print(context.get_context_summary())
# Output: "Trading on PHANTOM (Global Mode - All Assets)"
```

### Example 2: User on BTC Detail Page
```python
# User clicks "Trade Now" on BTC detail page
set_trading_context(
    exchange="phantom",
    asset="BTC",
    mode="asset_locked"
)

# Agent is now locked to BTC
context = get_trading_context()
print(context.get_context_summary())
# Output: "Trading BTC on PHANTOM (Asset-Locked Mode)"
```

### Example 3: User Switches Exchange
```python
# User was on Phantom, switches to Spot
update_exchange("spot")

# Context is preserved, only exchange changes
context = get_trading_context()
print(f"Now trading on {context.exchange}")
# Output: "Now trading on spot"
```

## Integration Points

### Frontend (React Native)
The frontend should call the backend API to update context when:
1. User switches exchange (header dropdown)
2. User navigates to Assist page (set global mode)
3. User clicks "Trade Now" on asset detail (set asset-locked mode)

### Backend API Endpoint (to be created)
```python
# POST /api/agent/context
{
    "exchange": "phantom",
    "asset": "BTC",
    "mode": "asset_locked"
}
```

### Agent System Prompt
The context should be injected into the agent's system prompt:
```python
from agents.context import get_context_for_agent
from agents.system_prompts import load_trading_agent_prompt

base_prompt = load_trading_agent_prompt()
context = get_context_for_agent()
full_prompt = f"{base_prompt}\n\n{context}"
```

## Notes

- Context is stored in-memory (singleton pattern)
- Context persists across agent calls within the same session
- Context is cleared when backend restarts
- For production, consider persisting context in database or Redis
- Asset symbols are automatically normalized to uppercase
- Exchange names are case-insensitive but stored as lowercase
