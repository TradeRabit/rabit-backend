# Agents Module

This module contains the AI agent system for Rabit trading platform.

## Structure

```
agents/
├── __init__.py              # Main module exports
├── README.md                # This file
│
├── core/                    # Core agent implementations
│   ├── base.py             # Base agent class
│   └── trading_agent.py    # Trading agent implementation
│
├── system_prompts/          # System prompts (easy to edit)
│   ├── __init__.py         # Prompt loaders
│   ├── trading_agent.txt   # Main trading agent prompt
│   ├── analysis_agent.txt  # Analysis specialist prompt
│   ├── risk_management.txt # Risk management prompt
│   └── README.md           # Prompt documentation
│
├── configs/                 # Agent configurations (JSON)
│   ├── __init__.py         # Config loaders
│   ├── trading_agent.json  # Trading agent config
│   ├── default_tools.json  # Tools configuration
│   └── README.md           # Config documentation
│
├── tools/                   # Tool implementations
│   ├── registry.py         # Tool registry
│   ├── definitions.py      # Tool definitions
│   ├── news_tools.py       # News monitoring tools
│   ├── price_monitor_tools.py  # Price alert tools
│   └── tradingview/        # TradingView integration
│
├── tools_registry/          # Tool registration
│   ├── __init__.py
│   └── register_tools.py   # Register all tools
│
├── memory/                  # Memory management
│   ├── conversation.py     # Conversation memory
│   ├── database.py         # Memory database
│   └── mem0_client.py      # Mem0 integration
│
├── compression/             # Message compression
│   └── compressor.py       # Conversation compressor
│
└── openrouter/             # OpenRouter integration
    └── models.py           # Model management
```

## Quick Start

### 1. Load System Prompt

```python
from agents.system_prompts import get_trading_agent_prompt

prompt = get_trading_agent_prompt()
```

### 2. Load Configuration

```python
from agents.configs import get_trading_agent_config

config = get_trading_agent_config()
```

### 3. Create Agent

```python
from agents import TradingAgent, register_trading_tools

# Register tools
register_trading_tools()

# Create agent
agent = TradingAgent(
    system_prompt=prompt,
    config=config
)
```

### 4. Use Agent

```python
# Chat with agent
response = await agent.chat("What's the current BTC price?")

# Use tools
await agent.execute_tool("get_price", {"symbol": "BTC"})
```

## Customization

### Edit System Prompts

System prompts are in `system_prompts/` as `.txt` files. Easy to edit without touching code:

```bash
# Edit trading agent prompt
nano agents/system_prompts/trading_agent.txt
```

### Edit Configurations

Configurations are in `configs/` as `.json` files:

```bash
# Edit trading agent config
nano agents/configs/trading_agent.json
```

### Add New Tools

1. Create tool function in `tools/`
2. Register in `tools_registry/register_tools.py`
3. Add to `configs/default_tools.json`

## Features

### System Prompts
- ✅ Separate files for easy editing
- ✅ No code changes needed
- ✅ Version controlled
- ✅ Multiple agent types

### Configurations
- ✅ JSON format
- ✅ Easy to customize
- ✅ Feature flags
- ✅ Resource limits

### Tools
- ✅ 33 trading tools
- ✅ Modular design
- ✅ Error handling
- ✅ Permission system

### Memory
- ✅ Conversation history
- ✅ Long-term memory
- ✅ Compression
- ✅ Database storage

## Development

### Adding New Agent Type

1. Create system prompt: `system_prompts/new_agent.txt`
2. Create config: `configs/new_agent.json`
3. Add loader functions in `__init__.py` files
4. Implement agent in `core/`

### Testing

```bash
# Test tools
python test/tools/test_*.py

# Test integration
python test/integration/test_*.py
```

## Best Practices

1. **System Prompts**
   - Keep focused and specific
   - Use clear examples
   - Update based on performance

2. **Configurations**
   - Use environment variables for secrets
   - Document all settings
   - Test before deployment

3. **Tools**
   - Comprehensive error handling
   - Clear documentation
   - Input validation

4. **Memory**
   - Regular cleanup
   - Compression for long conversations
   - Privacy considerations
