# OpenRouter Integration

## 📋 Overview

Rabit backend supports **OpenRouter** as an alternative to direct Anthropic API. OpenRouter provides:
- Access to 400+ AI models through a single API
- Cost-effective pricing (often cheaper than direct API)
- Automatic fallbacks and load balancing
- Free tier models available

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Claude API (Direct Anthropic)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OpenRouter (Alternative)
USE_OPENROUTER=true
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_SESSION_COST_DB_PATH=data/openrouter_session_costs.json
```

### Available Models

OpenRouter supports various Claude models:

| Model | OpenRouter ID | Use Case |
|-------|--------------|----------|
| Claude 3.5 Sonnet | `anthropic/claude-3.5-sonnet` | Best balance (recommended) |
| Claude 3 Opus | `anthropic/claude-3-opus` | Most capable |
| Claude 3 Sonnet | `anthropic/claude-3-sonnet` | Fast & capable |
| Claude 3 Haiku | `anthropic/claude-3-haiku` | Fastest & cheapest |

See all models: https://openrouter.ai/models?q=anthropic

### Other Providers

OpenRouter also supports non-Anthropic models:

```env
# Use OpenAI GPT-4
OPENROUTER_MODEL=openai/gpt-4-turbo

# Use Google Gemini
OPENROUTER_MODEL=google/gemini-pro

# Use Meta Llama
OPENROUTER_MODEL=meta-llama/llama-3-70b-instruct
```

## 🚀 Usage

### Option 1: Use Anthropic Direct (Default)

```env
USE_OPENROUTER=false
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

```python
from agents import TradingAgent

# Uses Anthropic API directly
agent = TradingAgent(scope_id="user_1")
response = await agent.process_trading_query("What's the price of SOL?")
```

### Option 2: Use OpenRouter

```env
USE_OPENROUTER=true
OPENROUTER_API_KEY=sk-or-xxxxx
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

```python
from agents import TradingAgent

# Uses OpenRouter (automatically configured)
agent = TradingAgent(scope_id="user_1")
response = await agent.process_trading_query("What's the price of SOL?")
```

**No code changes needed!** The agent automatically uses OpenRouter when `USE_OPENROUTER=true`.

## Session Cost Tracking

When OpenRouter is enabled, the backend can accumulate estimated usage cost per chat/session scope.

How it works:

1. the frontend sends a stable `scope_id` with chat requests
2. the agent records usage from router calls, main responses, tool follow-ups, streaming rounds, and compression
3. the backend stores the accumulated summary in `OPENROUTER_SESSION_COST_DB_PATH`
4. the latest accumulated summary is returned in:
   - `POST /api/agent/chat` as `session_cost`
   - the final `done` SSE event for `POST /api/agent/chat/stream`
   - `GET /api/openrouter/session-costs/{scope_id}`

Important notes:

- tracking is keyed by `scope_id`, not `user_id`
- if no `scope_id` is provided, session accumulation is skipped
- values are estimated using the locally stored OpenRouter model pricing data
- this summary is designed to feed downstream billing or contract-signing flows

## 💰 Cost Comparison

### Anthropic Direct API
- Claude 3.5 Sonnet: $3.00 / 1M input tokens, $15.00 / 1M output tokens
- Claude 3 Opus: $15.00 / 1M input tokens, $75.00 / 1M output tokens

### OpenRouter
- Claude 3.5 Sonnet: ~$3.00 / 1M input tokens, ~$15.00 / 1M output tokens
- Free tier models available (e.g., `google/gemini-flash-1.5`)
- Volume discounts available

**Savings**: OpenRouter can be 10-50% cheaper depending on usage patterns.

## 🔑 Getting OpenRouter API Key

1. Go to https://openrouter.ai/
2. Sign up for an account
3. Navigate to **Keys** section
4. Create a new API key
5. Copy the key (starts with `sk-or-`)
6. Add to `.env` file

## 📊 Features Supported

| Feature | Anthropic Direct | OpenRouter |
|---------|-----------------|------------|
| Chat completion | ✅ | ✅ |
| Tool calling | ✅ | ✅ |
| Streaming | ✅ | ✅ |
| Memory management | ✅ | ✅ |
| Auto-compression | ✅ | ✅ |
| System prompts | ✅ | ✅ |

**All features work identically** with both providers!

## 🔄 Switching Between Providers

You can switch between Anthropic and OpenRouter anytime:

```bash
# Switch to OpenRouter
export USE_OPENROUTER=true

# Switch back to Anthropic
export USE_OPENROUTER=false
```

Restart your application after changing.

## 🐛 Troubleshooting

### Error: "Invalid API key"

**Solution**: Check your API key format:
- Anthropic: `sk-ant-xxxxx`
- OpenRouter: `sk-or-xxxxx`

### Error: "Model not found"

**Solution**: Verify model ID at https://openrouter.ai/models

Correct format:
```env
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet  ✅
OPENROUTER_MODEL=claude-3.5-sonnet            ❌
```

### Error: "Rate limit exceeded"

**Solution**: 
1. Check your OpenRouter credits: https://openrouter.ai/credits
2. Add payment method or use free tier models
3. Implement rate limiting in your application

### Slow responses

**Solution**:
1. Try a faster model (e.g., `anthropic/claude-3-haiku`)
2. Check OpenRouter status: https://status.openrouter.ai/
3. Consider using Anthropic direct for critical workloads

## 📈 Best Practices

### 1. Use Environment-Specific Configuration

```env
# Development - use free/cheap models
USE_OPENROUTER=true
OPENROUTER_MODEL=google/gemini-flash-1.5

# Production - use best models
USE_OPENROUTER=false
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### 2. Monitor Costs

- Track usage at https://openrouter.ai/activity
- Set spending limits
- Use cheaper models for non-critical tasks

### 3. Implement Fallbacks

```python
# In production, you might want to implement fallbacks
try:
    # Try OpenRouter first
    response = await agent.process(query)
except Exception as e:
    # Fallback to Anthropic direct
    logger.warning(f"OpenRouter failed: {e}, falling back to Anthropic")
    # Switch to Anthropic and retry
```

### 4. Test Both Providers

Always test with both providers to ensure compatibility:

```bash
# Test with Anthropic
USE_OPENROUTER=false python test_agent.py

# Test with OpenRouter
USE_OPENROUTER=true python test_agent.py
```

## 🔗 Useful Links

- OpenRouter Docs: https://openrouter.ai/docs
- OpenRouter Models: https://openrouter.ai/models
- OpenRouter Pricing: https://openrouter.ai/docs/pricing
- Anthropic SDK: https://github.com/anthropics/anthropic-sdk-python
- OpenRouter Status: https://status.openrouter.ai/

## 📝 Example Configuration

### Complete `.env` Example

```env
# ============================================
# AI Provider Configuration
# ============================================

# Option 1: Use Anthropic Direct (Default)
USE_OPENROUTER=false
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Option 2: Use OpenRouter (Alternative)
# USE_OPENROUTER=true
# OPENROUTER_API_KEY=sk-or-xxxxx
# OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# ============================================
# Other Configuration
# ============================================

# Drift Protocol
DRIFT_RPC_URL=https://api.mainnet-beta.solana.com
DRIFT_PROGRAM_ID=dRiftyHA39MWEi3m9aunc5MzRF1JYJjb5ciH7N27eNn

# ... rest of config
```

## ✅ Summary

**OpenRouter Integration:**
- ✅ Fully compatible with Anthropic SDK
- ✅ No code changes required
- ✅ All features supported
- ✅ Easy switching between providers
- ✅ Cost-effective alternative
- ✅ Access to 400+ models

**When to use OpenRouter:**
- 💰 Want to save costs
- 🌍 Need access to multiple models
- 🔄 Want automatic fallbacks
- 🆓 Want to use free tier models

**When to use Anthropic Direct:**
- ⚡ Need lowest latency
- 🔒 Require direct SLA with Anthropic
- 🎯 Only need Claude models
- 💼 Enterprise requirements

---

**Last Updated**: 2026-04-14
**Version**: 1.0.0
