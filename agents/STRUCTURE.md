# Agents Module Structure

## Overview

Clean, organized structure with **NO implementation in init files**. All configurations and prompts are in separate, easy-to-edit files.

## Folder Structure

```
agents/
├── __init__.py                    # Clean imports only, NO implementation
├── README.md                      # Module documentation
├── STRUCTURE.md                   # This file
│
├── system_prompts/                # ✨ EASY TO EDIT - Just text files!
│   ├── __init__.py               # Loaders only, NO prompts here
│   ├── README.md                 # Prompt documentation
│   ├── trading_agent.txt         # Main trading agent prompt
│   ├── analysis_agent.txt        # Analysis specialist prompt
│   └── risk_management.txt       # Risk management prompt
│
├── configs/                       # ✨ EASY TO EDIT - JSON files!
│   ├── __init__.py               # Loaders only, NO configs here
│   ├── README.md                 # Config documentation
│   ├── trading_agent.json        # Agent settings
│   └── default_tools.json        # Tools configuration
│
├── context/                       # 🎯 Trading context management
│   ├── __init__.py               # Context exports
│   ├── README.md                 # Context documentation
│   └── trading_context.py        # Exchange, asset, mode tracking
│
├── core/                          # Agent implementations
│   ├── base.py                   # Base agent class
│   └── trading_agent.py          # Trading agent
│
├── tools/                         # Tool implementations
│   ├── registry.py
│   ├── definitions.py
│   ├── news_tools.py
│   ├── price_monitor_tools.py
│   └── tradingview/
│
├── tools_registry/                # Tool registration
│   ├── __init__.py
│   └── register_tools.py
│
├── memory/                        # Memory management
│   ├── conversation.py
│   ├── database.py
│   └── mem0_client.py
│
├── compression/                   # Message compression
│   └── compressor.py
│
└── openrouter/                   # OpenRouter integration
    └── models.py
```

## Key Principles

### ✅ NO Implementation in Init Files
- `__init__.py` files only contain imports and exports
- No actual code logic in init files
- Clean and maintainable

### ✅ Easy to Edit
- **System prompts**: Plain `.txt` files in `system_prompts/`
- **Configurations**: JSON files in `configs/`
- No need to touch Python code to change prompts or settings

### ✅ Organized by Function
- Each subfolder has clear purpose
- Related files grouped together
- Easy to find what you need

## Usage Examples

### Load System Prompt (from .txt file)

```python
from agents import get_trading_agent_prompt

# Loads from system_prompts/trading_agent.txt
prompt = get_trading_agent_prompt()
```

### Load Configuration (from .json file)

```python
from agents import get_trading_agent_config

# Loads from configs/trading_agent.json
config = get_trading_agent_config()
```

### Manage Trading Context

```python
from agents import set_trading_context, get_context_for_agent

# Set context (e.g., when user clicks "Trade Now" on BTC page)
set_trading_context(
    exchange="drift",
    asset="BTC",
    mode="asset_locked"
)

# Get formatted context for agent prompt
context_str = get_context_for_agent()
```

### Create Agent

```python
from agents import TradingAgent, register_trading_tools

# Register tools
register_trading_tools()

# Create agent with prompt and config
agent = TradingAgent(
    system_prompt=get_trading_agent_prompt(),
    config=get_trading_agent_config()
)
```

## Editing Guide

### To Edit System Prompt

1. Open `agents/system_prompts/trading_agent.txt`
2. Edit the text
3. Save
4. Restart agent

**No Python code changes needed!**

### To Edit Configuration

1. Open `agents/configs/trading_agent.json`
2. Edit JSON
3. Save
4. Restart agent

**No Python code changes needed!**

### To Add New Agent Type

1. Create prompt: `system_prompts/new_agent.txt`
2. Create config: `configs/new_agent.json`
3. Add loader in `system_prompts/__init__.py`:
   ```python
   def get_new_agent_prompt() -> str:
       return load_prompt("new_agent")
   ```
4. Add loader in `configs/__init__.py`:
   ```python
   def get_new_agent_config() -> Dict[str, Any]:
       return load_config("new_agent")
   ```
5. Export in `agents/__init__.py`

## Benefits

### For Developers
- Clean code structure
- Easy to navigate
- Clear separation of concerns
- No magic in init files

### For Users
- Easy to customize prompts
- Easy to adjust settings
- No Python knowledge needed for basic changes
- Version control friendly

### For Maintenance
- Easy to test
- Easy to debug
- Easy to extend
- Clear dependencies

## File Responsibilities

### `__init__.py` Files
- **ONLY** imports and exports
- **NO** implementation
- **NO** configuration
- **NO** prompts

### `.txt` Files (system_prompts/)
- System prompts for agents
- Plain text, easy to edit
- Version controlled
- No code

### `.json` Files (configs/)
- Agent configurations
- Settings and limits
- Tool permissions
- No code

### `.py` Files (other folders)
- Actual implementations
- Business logic
- Tool functions
- Agent classes

## Anti-Patterns (What NOT to Do)

❌ **Don't put prompts in init files**
```python
# BAD - Don't do this!
TRADING_PROMPT = """You are a trading agent..."""
```

❌ **Don't put configs in init files**
```python
# BAD - Don't do this!
CONFIG = {"model": "claude-3-5-sonnet", ...}
```

❌ **Don't put implementation in init files**
```python
# BAD - Don't do this!
def create_agent():
    # implementation here
    pass
```

✅ **Do use separate files**
```python
# GOOD - Do this!
from agents.system_prompts import get_trading_agent_prompt
from agents.configs import get_trading_agent_config
```

## Summary

- ✅ Clean structure
- ✅ Easy to edit (txt/json files)
- ✅ No implementation in init files
- ✅ Organized by function
- ✅ Maintainable and scalable
