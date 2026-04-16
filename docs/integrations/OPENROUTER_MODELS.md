# OpenRouter Models Management

## 📋 Overview

Rabit backend includes a comprehensive system for fetching, filtering, and managing AI models from OpenRouter. This allows you to:
- Fetch 400+ models from OpenRouter API
- Filter by capabilities (tool calling, reasoning)
- Filter by pricing, context length, provider
- Enable/disable specific models
- Get detailed model information

## 🔧 Features

### 1. **Automatic Model Fetching**
- Fetches all available models from OpenRouter API
- Caches results for 1 hour
- Force refresh option available

### 2. **Smart Filtering**
- **Tool Calling**: Filter models that support function/tool calling
- **Reasoning**: Filter models that support reasoning/thinking
- **Context Length**: Minimum context length requirement
- **Pricing**: Maximum input/output price per 1M tokens
- **Provider**: Filter by provider (anthropic, openai, google, etc.)
- **Enabled Status**: Show only enabled models

### 3. **Model Management**
- Enable/disable specific models
- Track enabled models
- Get model statistics

### 4. **Detailed Information**
For each model, you get:
- Model ID and name
- Description
- Context length
- Input/output pricing (per 1M tokens)
- Tool calling support
- Reasoning support
- Knowledge cutoff date
- Release date
- Modality (text, image, audio, etc.)
- Tokenizer type

## 📊 API Endpoints

### 1. List Models with Filtering

```http
GET /api/models
```

**Query Parameters:**
- `require_tools` (boolean): Only models with tool calling support
- `require_reasoning` (boolean): Only models with reasoning support
- `min_context` (integer): Minimum context length
- `max_input_price` (float): Maximum input price per 1M tokens (USD)
- `max_output_price` (float): Maximum output price per 1M tokens (USD)
- `provider` (string): Filter by provider (e.g., 'anthropic', 'openai')
- `enabled_only` (boolean): Only enabled models (default: true)
- `refresh` (boolean): Force refresh from API (default: false)

**Example Requests:**

```bash
# Get all models with tool calling support
curl "http://localhost:8000/api/models?require_tools=true"

# Get Anthropic models with reasoning support
curl "http://localhost:8000/api/models?provider=anthropic&require_reasoning=true"

# Get cheap models (max $5 per 1M tokens)
curl "http://localhost:8000/api/models?max_input_price=5&max_output_price=5"

# Get models with large context (min 100k tokens)
curl "http://localhost:8000/api/models?min_context=100000"

# Force refresh from OpenRouter
curl "http://localhost:8000/api/models?refresh=true"
```

**Response:**

```json
{
  "models": [
    {
      "id": "anthropic/claude-3.5-sonnet",
      "name": "Anthropic: Claude 3.5 Sonnet",
      "provider": "anthropic",
      "description": "Claude 3.5 Sonnet...",
      "context_length": 200000,
      "input_price": 3.0,
      "output_price": 15.0,
      "supports_tools": true,
      "supports_reasoning": true,
      "knowledge_cutoff": "2024-04-30",
      "created": 1712620800,
      "modality": "text->text",
      "tokenizer": "Claude",
      "enabled": true
    }
  ],
  "total": 45,
  "enabled": 40,
  "disabled": 5,
  "last_updated": "2026-04-14T10:30:00Z"
}
```

### 2. Get Models Grouped by Provider

```http
GET /api/models/grouped
```

**Query Parameters:**
- `enabled_only` (boolean): Only enabled models (default: true)
- `require_tools` (boolean): Only models with tool calling support
- `require_reasoning` (boolean): Only models with reasoning support

**Example:**

```bash
# Get all models grouped by provider
curl "http://localhost:8000/api/models/grouped"

# Get only models with tool calling, grouped by provider
curl "http://localhost:8000/api/models/grouped?require_tools=true"
```

**Response:**

```json
{
  "grouped": {
    "anthropic": [
      {
        "id": "anthropic/claude-3.5-sonnet",
        "name": "Anthropic: Claude 3.5 Sonnet",
        "provider": "anthropic",
        "context_length": 200000,
        "input_price": 3.0,
        "output_price": 15.0,
        "supports_tools": true,
        "supports_reasoning": true,
        "enabled": true
      },
      {
        "id": "anthropic/claude-3-opus",
        "name": "Anthropic: Claude 3 Opus",
        "provider": "anthropic",
        "context_length": 200000,
        "input_price": 15.0,
        "output_price": 75.0,
        "supports_tools": true,
        "supports_reasoning": false,
        "enabled": true
      }
    ],
    "openai": [
      {
        "id": "openai/gpt-4-turbo",
        "name": "OpenAI: GPT-4 Turbo",
        "provider": "openai",
        "context_length": 128000,
        "input_price": 10.0,
        "output_price": 30.0,
        "supports_tools": true,
        "supports_reasoning": false,
        "enabled": true
      }
    ]
  },
  "provider_stats": {
    "anthropic": {
      "total": 5,
      "with_tools": 5,
      "with_reasoning": 2
    },
    "openai": {
      "total": 12,
      "with_tools": 8,
      "with_reasoning": 1
    }
  },
  "total_providers": 15
}
```

### 3. Get List of Providers

```http
GET /api/models/providers
```

**Response:**

```json
{
  "providers": [
    "anthropic",
    "google",
    "meta-llama",
    "mistralai",
    "openai"
  ],
  "total": 5
}
```

### 4. Get Model Statistics

```http
GET /api/models/stats
```

**Response:**

```json
{
  "total_models": 400,
  "enabled_models": 350,
  "disabled_models": 50,
  "models_with_tools": 120,
  "models_with_reasoning": 45,
  "providers": {
    "anthropic": {
      "total": 8,
      "enabled": 7,
      "with_tools": 8,
      "with_reasoning": 3
    },
    "openai": {
      "total": 15,
      "enabled": 12,
      "with_tools": 10,
      "with_reasoning": 2
    },
    "google": {
      "total": 6,
      "enabled": 5,
      "with_tools": 4,
      "with_reasoning": 0
    }
  },
  "last_updated": "2026-04-14T10:30:00Z"
}
```

### 5. Get Specific Model Info

```http
GET /api/models/{model_id}
```

**Example:**

```bash
curl "http://localhost:8000/api/models/anthropic/claude-3.5-sonnet"
```

**Response:**

```json
{
  "id": "anthropic/claude-3.5-sonnet",
  "name": "Anthropic: Claude 3.5 Sonnet",
  "provider": "anthropic",
  "description": "Claude 3.5 Sonnet is Anthropic's most intelligent model...",
  "context_length": 200000,
  "input_price": 3.0,
  "output_price": 15.0,
  "supports_tools": true,
  "supports_reasoning": true,
  "knowledge_cutoff": "2024-04-30",
  "created": 1712620800,
  "modality": "text->text",
  "tokenizer": "Claude",
  "enabled": true
}
```

### 6. Enable/Disable Model

```http
POST /api/models/toggle
```

**Request Body:**

```json
{
  "model_id": "anthropic/claude-3.5-sonnet",
  "enabled": true
}
```

**Response:**

```json
{
  "success": true,
  "model_id": "anthropic/claude-3.5-sonnet",
  "enabled": true,
  "message": "Model enabled successfully"
}
```

## 💻 Python Usage

### Fetch and Filter Models

```python
from agents.openrouter import get_openrouter_models

# Get models manager
models_manager = get_openrouter_models()

# Fetch models from OpenRouter
await models_manager.fetch_models()

# Filter models with tool calling support
tool_models = models_manager.filter_models(require_tools=True)

# Filter Anthropic models with reasoning
anthropic_reasoning = models_manager.filter_models(
    provider="anthropic",
    require_reasoning=True
)

# Filter cheap models
cheap_models = models_manager.filter_models(
    max_input_price=5.0,
    max_output_price=10.0
)

# Filter by context length
large_context = models_manager.filter_models(min_context=100000)

# Combine filters
best_models = models_manager.filter_models(
    require_tools=True,
    require_reasoning=True,
    min_context=100000,
    provider="anthropic"
)
```

### Manage Models

```python
# Get specific model
model = models_manager.get_model("anthropic/claude-3.5-sonnet")
print(f"Model: {model.name}")
print(f"Price: ${model.input_price}/1M input, ${model.output_price}/1M output")
print(f"Supports tools: {model.supports_tools}")

# Enable/disable models
models_manager.enable_model("anthropic/claude-3.5-sonnet")
models_manager.disable_model("openai/gpt-3.5-turbo")

# Get enabled models only
enabled = models_manager.get_enabled_models()
print(f"Enabled models: {len(enabled)}")

# Get statistics
stats = models_manager.get_stats()
print(f"Total: {stats['total_models']}")
print(f"With tools: {stats['models_with_tools']}")
print(f"With reasoning: {stats['models_with_reasoning']}")
```

## 🎯 Use Cases

### 1. Find Best Model for Trading Agent

```python
# Requirements: tool calling, reasoning, large context, reasonable price
trading_models = models_manager.filter_models(
    require_tools=True,
    require_reasoning=True,
    min_context=100000,
    max_input_price=10.0,
    max_output_price=30.0
)

# Sort by price (cheapest first)
trading_models.sort(key=lambda m: m.input_price + m.output_price)

# Use the best model
best_model = trading_models[0]
print(f"Best model: {best_model.id}")
```

### 2. Find Free/Cheap Models

```python
# Find models under $1 per 1M tokens
free_models = models_manager.filter_models(
    max_input_price=1.0,
    max_output_price=1.0
)

print(f"Found {len(free_models)} cheap models")
for model in free_models:
    print(f"- {model.name}: ${model.input_price + model.output_price}/1M tokens")
```

### Compare Providers

```python
# Get models grouped by provider
grouped = models_manager.get_models_by_provider(enabled_only=True)

for provider, models in grouped.items():
    print(f"\n{provider.upper()}:")
    print(f"  Total models: {len(models)}")
    print(f"  With tools: {len([m for m in models if m.supports_tools])}")
    print(f"  With reasoning: {len([m for m in models if m.supports_reasoning])}")
    
    # Show cheapest model
    cheapest = min(models, key=lambda m: m.input_price + m.output_price)
    print(f"  Cheapest: {cheapest.name} (${cheapest.input_price + cheapest.output_price}/1M)")

# Get list of all providers
providers = models_manager.get_providers()
print(f"\nAvailable providers: {', '.join(providers)}")
```

### 4. Find Models by Capability

```python
# Models with tool calling
tool_models = models_manager.filter_models(require_tools=True)
print(f"Models with tool calling: {len(tool_models)}")

# Models with reasoning
reasoning_models = models_manager.filter_models(require_reasoning=True)
print(f"Models with reasoning: {len(reasoning_models)}")

# Models with both
both = models_manager.filter_models(
    require_tools=True,
    require_reasoning=True
)
print(f"Models with both: {len(both)}")
```

## 📈 Model Capabilities

### Tool Calling Support

Models that support `tools` or `tool_choice` parameters:
- Anthropic Claude 3.x series
- OpenAI GPT-4, GPT-3.5 Turbo
- Google Gemini Pro
- Mistral Large
- And more...

### Reasoning Support

Models that support `reasoning` or `include_reasoning` parameters:
- OpenAI o1 series
- Anthropic Claude 3.5 Sonnet (extended thinking)
- Some specialized reasoning models

## 💡 Best Practices

### 1. Cache Models

```python
# Fetch once, use multiple times
await models_manager.fetch_models()

# Subsequent calls use cache (1 hour)
models1 = models_manager.filter_models(require_tools=True)
models2 = models_manager.filter_models(provider="anthropic")
# No additional API calls
```

### 2. Enable Only Needed Models

```python
# Disable expensive models if not needed
expensive_models = models_manager.filter_models(min_input_price=20.0)
for model in expensive_models:
    models_manager.disable_model(model.id)

# Enable only specific models
allowed_models = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-haiku",
    "openai/gpt-4-turbo"
]
for model_id in allowed_models:
    models_manager.enable_model(model_id)
```

### 3. Monitor Costs

```python
# Get enabled models and calculate potential costs
enabled = models_manager.get_enabled_models()

total_input_cost = sum(m.input_price for m in enabled)
total_output_cost = sum(m.output_price for m in enabled)

print(f"Average input cost: ${total_input_cost / len(enabled):.2f}/1M tokens")
print(f"Average output cost: ${total_output_cost / len(enabled):.2f}/1M tokens")
```

### 4. Refresh Periodically

```python
# Force refresh to get latest models
await models_manager.fetch_models(force_refresh=True)

# Or use API endpoint
# GET /api/models?refresh=true
```

## 🔗 Integration with Agent

```python
from agents import TradingAgent
from agents.openrouter import get_openrouter_models

# Get best model for trading
models_manager = get_openrouter_models()
await models_manager.fetch_models()

trading_models = models_manager.filter_models(
    require_tools=True,
    require_reasoning=True,
    provider="anthropic"
)

# Use the best model
best_model = trading_models[0]

# Configure agent to use this model
import os
os.environ["USE_OPENROUTER"] = "true"
os.environ["OPENROUTER_MODEL"] = best_model.id

# Create agent (will use the configured model)
agent = TradingAgent(scope_id="user_1")
```

## 📊 Model Comparison Table

| Provider | Model | Tools | Reasoning | Context | Input $/1M | Output $/1M |
|----------|-------|-------|-----------|---------|------------|-------------|
| Anthropic | Claude 3.5 Sonnet | ✅ | ✅ | 200k | $3.00 | $15.00 |
| Anthropic | Claude 3 Opus | ✅ | ❌ | 200k | $15.00 | $75.00 |
| Anthropic | Claude 3 Haiku | ✅ | ❌ | 200k | $0.25 | $1.25 |
| OpenAI | GPT-4 Turbo | ✅ | ❌ | 128k | $10.00 | $30.00 |
| OpenAI | GPT-3.5 Turbo | ✅ | ❌ | 16k | $0.50 | $1.50 |
| Google | Gemini Pro | ✅ | ❌ | 32k | $0.50 | $1.50 |
| Mistral | Mistral Large | ✅ | ❌ | 128k | $2.00 | $6.00 |

*Prices are approximate and may vary*

## ✅ Summary

**OpenRouter Models Management:**
- ✅ Fetch 400+ models from OpenRouter API
- ✅ Filter by tool calling support
- ✅ Filter by reasoning support
- ✅ Filter by pricing, context, provider
- ✅ Enable/disable specific models
- ✅ Get detailed model information
- ✅ REST API endpoints
- ✅ Python SDK
- ✅ Automatic caching (1 hour)

**Perfect for:**
- Finding the best model for your use case
- Cost optimization
- Capability-based selection
- Multi-model strategies

---

**Last Updated**: 2026-04-14
**Version**: 1.0.0



## 💾 Persistent Database

### Overview

Models are stored permanently in a JSON database (`data/openrouter_models.json`) to avoid repeated API calls and improve performance.

### Database Behavior

1. **First Load**: Fetches from OpenRouter API and saves to database
2. **Subsequent Loads**: Reads from database (instant)
3. **Staleness Check**: Database is considered stale after 7 days
4. **Auto Refresh**: Automatically refreshes if stale
5. **Fallback**: Uses database even if API fails

### Database Endpoints

#### Get Database Statistics

```http
GET /api/models/database/stats
```

**Response:**

```json
{
  "total_models": 400,
  "last_updated": "2026-04-14T10:30:00Z",
  "is_stale": false,
  "providers": 15,
  "models_with_tools": 120,
  "models_with_reasoning": 45
}
```

#### Force Refresh Database

```http
POST /api/models/database/refresh
```

Forces a refresh from OpenRouter API and updates the database.

**Response:**

```json
{
  "success": true,
  "message": "Database refreshed successfully",
  "total_models": 400,
  "timestamp": "2026-04-14T10:30:00Z"
}
```

#### Clear Database

```http
DELETE /api/models/database/clear
```

Clears all models from database. Will be refetched on next request.

**Response:**

```json
{
  "success": true,
  "message": "Database cleared successfully"
}
```

### Python Usage

```python
from agents.openrouter import get_models_database

# Get database instance
db = get_models_database()

# Check if stale
if db.is_stale():
    print("Database is stale, will refresh on next fetch")

# Get stats
stats = db.get_stats()
print(f"Total models: {stats['total_models']}")
print(f"Last updated: {stats['last_updated']}")
print(f"Is stale: {stats['is_stale']}")

# Get all models from database (instant)
models = db.get_all_models()
print(f"Loaded {len(models)} models from database")

# Clear database
db.clear()
```

### Performance Benefits

| Operation | Without Database | With Database |
|-----------|-----------------|---------------|
| First load | ~2-3 seconds | ~2-3 seconds |
| Subsequent loads | ~2-3 seconds | ~0.01 seconds |
| API failures | Error | Works (uses cache) |
| Offline mode | Not possible | Works |

### Database Configuration

```python
# Default location
db = get_models_database()  # data/openrouter_models.json

# Custom location
db = get_models_database("custom/path/models.json")

# Check staleness (default: 7 days)
is_stale = db.is_stale(max_age_days=7)

# Force refresh
models_manager = get_openrouter_models()
await models_manager.fetch_models(force_refresh=True)
```

### Best Practices

1. **Let it Auto-Refresh**: Database auto-refreshes when stale (7 days)
2. **Manual Refresh**: Only force refresh when needed (new models released)
3. **Backup Database**: Keep backup of `data/openrouter_models.json`
4. **Monitor Staleness**: Check database stats periodically

### Troubleshooting

**Database not loading?**
```bash
# Check if file exists
ls -la data/openrouter_models.json

# Check file permissions
chmod 644 data/openrouter_models.json

# Force refresh
curl -X POST http://localhost:8000/api/models/database/refresh
```

**Database corrupted?**
```bash
# Clear and refresh
curl -X DELETE http://localhost:8000/api/models/database/clear
curl -X POST http://localhost:8000/api/models/database/refresh
```

**Want to update manually?**
```python
from agents.openrouter import get_openrouter_models

models_manager = get_openrouter_models()
await models_manager.fetch_models(force_refresh=True)
```

---

**Database Features:**
- ✅ Persistent JSON storage
- ✅ Auto-refresh when stale (7 days)
- ✅ Instant loading from cache
- ✅ Fallback on API failure
- ✅ Enable/disable state persisted
- ✅ Manual refresh option
- ✅ Clear database option
- ✅ Statistics tracking
