# Assistant Types - Global vs Asset-Specific

## Overview

Rabit memiliki 2 jenis assistant:

### 1. Global Assistant
- **Path:** `/app/assist.tsx`
- **Scope:** General trading assistant
- **Context:** No specific asset context
- **Use Case:** General questions, portfolio overview, trading strategies

### 2. Asset-Specific Assistant  
- **Path:** `/app/asset-detail/[id]/assist.tsx`
- **Scope:** Asset-specific assistant
- **Context:** Specific asset (BTC, ETH, SOL, etc.)
- **Use Case:** Asset-specific analysis, price predictions, trading signals

## Backend Implementation

### Agent Scope ID

Backend menggunakan `scope_id` untuk membedakan conversation context:

```python
# Global Assistant
agent = TradingAgent(scope_id="global")

# Asset-Specific Assistant
agent = TradingAgent(scope_id="asset:BTC")
agent = TradingAgent(scope_id="asset:ETH")
agent = TradingAgent(scope_id="asset:SOL")
```

### Memory Isolation

Setiap scope memiliki memory terpisah:

```python
# Global conversation
global_agent = TradingAgent(scope_id="global")
await global_agent.process_trading_query("What's the market trend?")

# BTC-specific conversation
btc_agent = TradingAgent(scope_id="asset:BTC")
await btc_agent.process_trading_query("Should I buy BTC now?")

# ETH-specific conversation  
eth_agent = TradingAgent(scope_id="asset:ETH")
await eth_agent.process_trading_query("What's ETH price target?")
```

## API Endpoints

### Global Assistant

```http
POST /api/agent/chat
Content-Type: application/json

{
  "scope_id": "global",
  "message": "What's the market trend today?"
}
```

### Asset-Specific Assistant

```http
POST /api/agent/chat
Content-Type: application/json

{
  "scope_id": "asset:BTC",
  "message": "Should I buy BTC now?"
}
```

## System Prompts

### Global Assistant

```python
system_prompt = """You are Rabit Agent, a helpful trading assistant.

Your capabilities:
- Market overview and analysis
- Portfolio management
- General trading advice
- Multi-asset comparison

Be helpful and professional."""
```

### Asset-Specific Assistant

```python
system_prompt = f"""You are Rabit Agent, specialized in {asset_symbol} trading.

Context: User is viewing {asset_symbol} detail page.

Your capabilities:
- {asset_symbol}-specific price analysis
- {asset_symbol} trading signals
- {asset_symbol} market sentiment
- {asset_symbol} technical indicators

Focus on {asset_symbol} and provide actionable insights."""
```

## Tools Context

### Global Assistant Tools

- `get_price(symbol)` - Any symbol
- `get_portfolio()` - User portfolio
- `compare_assets(symbols)` - Multi-asset comparison

### Asset-Specific Assistant Tools

- `get_price(symbol)` - Pre-filled with current asset
- `get_technical_indicators(symbol)` - Pre-filled with current asset
- `get_trading_signals(symbol)` - Pre-filled with current asset

## Implementation Example

### Backend API Route

```python
@router.post("/api/agent/chat")
async def agent_chat(request: ChatRequest):
    scope_id = request.scope_id
    message = request.message
    
    # Determine assistant type
    if scope_id == "global":
        # Global assistant
        agent = TradingAgent(scope_id="global")
    elif scope_id.startswith("asset:"):
        # Asset-specific assistant
        asset_symbol = scope_id.split(":")[1]
        agent = TradingAgent(
            scope_id=scope_id,
            system_prompt=get_asset_specific_prompt(asset_symbol)
        )
    
    # Process message
    response = await agent.process_trading_query(message)
    
    return {"response": response}
```

### Mobile Integration

```typescript
// Global Assistant
const globalChat = async (message: string) => {
  const response = await fetch('/api/agent/chat', {
    method: 'POST',
    body: JSON.stringify({
      scope_id: 'global',
      message: message
    })
  });
  return response.json();
};

// Asset-Specific Assistant
const assetChat = async (assetId: string, message: string) => {
  const response = await fetch('/api/agent/chat', {
    method: 'POST',
    body: JSON.stringify({
      scope_id: `asset:${assetId}`,
      message: message
    })
  });
  return response.json();
};
```

## Benefits

### Memory Isolation
- ✅ Global conversations don't mix with asset-specific
- ✅ Each asset has its own conversation history
- ✅ Clear context separation

### Context Awareness
- ✅ Asset-specific assistant knows current asset
- ✅ Can provide more relevant answers
- ✅ Pre-filled tool parameters

### User Experience
- ✅ Seamless transition between assistants
- ✅ Relevant suggestions based on context
- ✅ Faster responses (no need to specify asset)

## Status

- ✅ Global Assistant: Implemented in mobile
- ⏳ Asset-Specific Assistant: Placeholder (coming soon)
- ✅ Backend: Ready to support both types
- ✅ Memory System: Supports scope isolation

---

**Last Updated:** 2026-04-14
**Version:** 1.0.0
