# Mem0 Integration - User Memory Management

## Overview

Mem0 adalah self-hosted memory service untuk menyimpan user-specific information seperti trading preferences, balance limits, risk tolerance, dll.

## Architecture

```
┌─────────────────┐
│  Rabit Backend  │
│                 │
│  ┌───────────┐  │
│  │   Agent   │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │Mem0 Client│  │
│  └─────┬─────┘  │
└────────┼────────┘
         │ HTTP
┌────────▼────────┐
│   Mem0 Service  │
│   (Docker)      │
└────────┬────────┘
         │
┌────────▼────────┐
│     Qdrant      │
│ (Vector DB)     │
└─────────────────┘
```

## Features

✅ **Self-Hosted** - Runs in Docker, no external dependencies
✅ **Vector Search** - Semantic search using Qdrant
✅ **User-Specific** - Isolated memory per user
✅ **Persistent** - Data survives restarts
✅ **Fast** - In-memory vector search
✅ **Privacy** - All data stays on your server

## Use Cases

### 1. Trading Balance Limits
```python
# User sets trading limit
await mem0.add_memory(
    user_id="user_123",
    text="My maximum trading balance is $10,000 per trade"
)

# Agent retrieves limit
context = await mem0.get_context(user_id="user_123", query="trading balance")
# Returns: "User Information:\n- My maximum trading balance is $10,000 per trade"
```

### 2. Risk Preferences
```python
await mem0.add_memory(
    user_id="user_123",
    text="I prefer low-risk trades with maximum 2% stop loss"
)
```

### 3. Favorite Assets
```python
await mem0.add_memory(
    user_id="user_123",
    text="My favorite trading assets are BTC, ETH, and SOL"
)
```

### 4. Trading Strategy
```python
await mem0.add_memory(
    user_id="user_123",
    text="I use DCA strategy and buy dips on weekends"
)
```

### 5. Personal Notes
```python
await mem0.add_memory(
    user_id="user_123",
    text="Avoid trading during US market hours due to high volatility"
)
```

## Setup

### Docker Compose

Already configured in `docker-compose.yml`:

```yaml
services:
  # Mem0 Service
  mem0:
    image: mem0ai/mem0:latest
    ports:
      - "8080:8080"
    environment:
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
    depends_on:
      - qdrant

  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
```

### Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs mem0
docker-compose logs qdrant
```

### Environment Variables

```bash
# .env
MEM0_ENABLED=true
MEM0_HOST=localhost
MEM0_PORT=8080
```

## Python API

### Initialize Client

```python
from agents.memory import Mem0Client, get_mem0_client

# Get singleton instance
mem0 = get_mem0_client()
```

### Add Memory

```python
# Add user memory
result = await mem0.add_memory(
    user_id="user_123",
    text="My trading balance limit is $10,000",
    metadata={"category": "balance", "priority": "high"}
)

if result["success"]:
    print(f"Memory added: {result['data']}")
```

### Search Memories

```python
# Search for specific information
memories = await mem0.search_memories(
    user_id="user_123",
    query="trading balance",
    limit=5
)

for memory in memories:
    print(f"- {memory['text']}")
```

### Get All Memories

```python
# Get all memories for user
all_memories = await mem0.get_all_memories(user_id="user_123")

print(f"Total memories: {len(all_memories)}")
for memory in all_memories:
    print(f"- {memory['text']}")
```

### Get Context for Agent

```python
# Get relevant context for agent query
context = await mem0.get_context(
    user_id="user_123",
    query="What's my trading limit?"
)

# Use context in agent prompt
system_prompt = f"""You are a trading assistant.

{context}

Answer the user's question based on their preferences."""
```

### Delete Memory

```python
# Delete specific memory
success = await mem0.delete_memory(
    user_id="user_123",
    memory_id="mem_abc123"
)

# Delete all memories
success = await mem0.delete_all_memories(user_id="user_123")
```

## Agent Integration

### TradingAgent with Mem0

```python
from agents import TradingAgent
from agents.memory import get_mem0_client

class TradingAgentWithMem0(TradingAgent):
    def __init__(self, user_id: str, scope_id: Optional[str] = None):
        super().__init__(scope_id=scope_id)
        self.user_id = user_id
        self.mem0 = get_mem0_client()
    
    async def process_with_context(self, user_input: str) -> str:
        # Get user context from Mem0
        context = await self.mem0.get_context(
            user_id=self.user_id,
            query=user_input
        )
        
        # Add context to system prompt
        if context:
            enhanced_prompt = f"{self.system_prompt}\n\n{context}"
            self.system_prompt = enhanced_prompt
        
        # Process query
        return await self.process_trading_query(user_input)
```

### Usage Example

```python
# Create agent with user context
agent = TradingAgentWithMem0(
    user_id="user_123",
    scope_id="global"
)

# User asks about trading
response = await agent.process_with_context(
    "Should I buy BTC now?"
)

# Agent has access to:
# - User's trading balance limit
# - User's risk preferences
# - User's favorite assets
# - User's trading strategy
```

## API Endpoints

### Add Memory

```http
POST /api/memory
Content-Type: application/json

{
  "user_id": "user_123",
  "text": "My trading balance limit is $10,000",
  "metadata": {"category": "balance"}
}
```

### Search Memories

```http
GET /api/memory/search?user_id=user_123&query=trading+balance&limit=5
```

### Get All Memories

```http
GET /api/memory?user_id=user_123
```

### Delete Memory

```http
DELETE /api/memory/{memory_id}?user_id=user_123
```

### Delete All Memories

```http
DELETE /api/memory?user_id=user_123
```

## Best Practices

### 1. Use Clear, Descriptive Text

```python
# ✅ GOOD: Clear and specific
await mem0.add_memory(
    user_id="user_123",
    text="My maximum trading balance per trade is $10,000"
)

# ❌ BAD: Vague
await mem0.add_memory(
    user_id="user_123",
    text="10k limit"
)
```

### 2. Add Metadata for Organization

```python
await mem0.add_memory(
    user_id="user_123",
    text="My trading balance limit is $10,000",
    metadata={
        "category": "balance",
        "priority": "high",
        "created_by": "user",
        "source": "settings"
    }
)
```

### 3. Update Instead of Duplicate

```python
# Delete old memory first
old_memories = await mem0.search_memories(
    user_id="user_123",
    query="trading balance limit"
)

for memory in old_memories:
    await mem0.delete_memory(user_id="user_123", memory_id=memory["id"])

# Add new memory
await mem0.add_memory(
    user_id="user_123",
    text="My new trading balance limit is $20,000"
)
```

### 4. Use Semantic Search

```python
# Mem0 uses vector search, so similar queries work
await mem0.search_memories(user_id="user_123", query="trading limit")
await mem0.search_memories(user_id="user_123", query="maximum balance")
await mem0.search_memories(user_id="user_123", query="how much can I trade")
# All return the same memory!
```

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Add memory | < 0.1s | Vector embedding + storage |
| Search memories | < 0.05s | Vector similarity search |
| Get all memories | < 0.01s | Direct retrieval |
| Delete memory | < 0.01s | Direct deletion |

## Storage

- **Qdrant**: Stores vectors and metadata
- **Volume**: `qdrant_data` (persistent across restarts)
- **Size**: ~1 KB per memory
- **Capacity**: Millions of memories

## Troubleshooting

### Mem0 Not Starting

```bash
# Check logs
docker-compose logs mem0

# Restart service
docker-compose restart mem0
```

### Qdrant Connection Error

```bash
# Check Qdrant status
docker-compose logs qdrant

# Restart Qdrant
docker-compose restart qdrant
```

### Memory Not Found

```python
# Check if Mem0 is enabled
from config.settings import settings
print(f"Mem0 enabled: {settings.MEM0_ENABLED}")

# Check connection
mem0 = get_mem0_client()
memories = await mem0.get_all_memories(user_id="user_123")
print(f"Total memories: {len(memories)}")
```

## Disable Mem0

```bash
# In .env
MEM0_ENABLED=false

# Or in docker-compose.yml, comment out mem0 and qdrant services
```

## Summary

✅ **Self-Hosted** - Runs in Docker
✅ **User-Specific** - Isolated per user
✅ **Semantic Search** - Vector-based search
✅ **Persistent** - Survives restarts
✅ **Fast** - < 0.1s operations
✅ **Privacy** - All data on your server
✅ **Easy Integration** - Simple Python API

**Use Cases:**
- Trading balance limits
- Risk preferences
- Favorite assets
- Trading strategies
- Personal notes

---

**Last Updated:** 2026-04-14
**Version:** 1.0.0
**Status:** ✅ Production Ready
