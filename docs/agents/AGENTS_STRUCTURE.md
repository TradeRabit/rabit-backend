# Agents Module Structure

## 📁 Organized Folder Structure

```
agents/
├── __init__.py                 # Main module exports
├── core/                       # Core agent implementations
│   ├── __init__.py
│   ├── base.py                # BaseAgent class
│   └── trading_agent.py       # TradingAgent example
├── memory/                     # Memory management
│   ├── __init__.py
│   └── conversation.py        # ConversationMemory & Message
├── compression/               # Auto compression
│   ├── __init__.py
│   └── compressor.py          # ConversationCompressor
├── tools/                      # Tool system
│   ├── __init__.py
│   ├── definitions.py         # ToolDefinition, ToolParameter, ToolResult
│   └── registry.py            # ToolRegistry & tool_registry
└── examples/                   # Example implementations
    ├── __init__.py
    └── trading_tools.py       # Example trading tools
```

## 🎯 Module Organization by Feature

### 1. **Core Module** (`agents/core/`)
**Purpose**: Core agent implementations

**Files**:
- `base.py` - BaseAgent class with all features
- `trading_agent.py` - TradingAgent example

**Exports**:
```python
from agents.core import BaseAgent, TradingAgent
```

**Features**:
- Agent initialization
- Message management
- Tool calling
- Auto-compression integration
- Memory integration

### 2. **Memory Module** (`agents/memory/`)
**Purpose**: Conversation memory management

**Files**:
- `conversation.py` - ConversationMemory & Message classes

**Exports**:
```python
from agents.memory import ConversationMemory, Message
```

**Features**:
- Global memory storage
- Scoped memory per user/session
- Message history with timestamps
- Memory operations (add, get, clear)

### 3. **Compression Module** (`agents/compression/`)
**Purpose**: Auto conversation compression

**Files**:
- `compressor.py` - ConversationCompressor class

**Exports**:
```python
from agents.compression import ConversationCompressor
```

**Features**:
- Token counting
- Compression detection
- Smart summarization
- Fallback truncation

### 4. **Tools Module** (`agents/tools/`)
**Purpose**: Tool system with registry

**Files**:
- `definitions.py` - Tool models (ToolDefinition, ToolParameter, ToolResult)
- `registry.py` - ToolRegistry & global instance

**Exports**:
```python
from agents.tools import (
    ToolRegistry,
    ToolDefinition,
    ToolParameter,
    ToolResult,
    tool_registry
)
```

**Features**:
- Tool registration
- Parameter validation
- Tool execution
- Detailed error handling

### 5. **Examples Module** (`agents/examples/`)
**Purpose**: Example tools and agents

**Files**:
- `trading_tools.py` - Example trading tools

**Exports**:
```python
from agents.examples import register_example_tools
```

**Features**:
- 3 example tools (market price, position size, account info)
- Tool registration helper

## 🔄 Import Patterns

### From Main Module
```python
from agents import (
    BaseAgent,
    TradingAgent,
    ConversationMemory,
    Message,
    ConversationCompressor,
    ToolRegistry,
    ToolDefinition,
    ToolParameter,
    ToolResult,
    tool_registry,
    register_example_tools
)
```

### From Submodules
```python
# Core
from agents.core import BaseAgent, TradingAgent

# Memory
from agents.memory import ConversationMemory, Message

# Compression
from agents.compression import ConversationCompressor

# Tools
from agents.tools import (
    ToolRegistry,
    ToolDefinition,
    ToolParameter,
    ToolResult,
    tool_registry
)

# Examples
from agents.examples import register_example_tools
```

## 📊 Dependency Graph

```
agents/
├── core/
│   ├── base.py
│   │   ├── imports: memory, compression, tools
│   │   └── uses: ConversationMemory, ConversationCompressor, tool_registry
│   └── trading_agent.py
│       └── imports: base
│
├── memory/
│   └── conversation.py
│       └── standalone (no internal dependencies)
│
├── compression/
│   └── compressor.py
│       └── standalone (external: anthropic, tiktoken)
│
├── tools/
│   ├── definitions.py
│   │   └── standalone (external: pydantic)
│   └── registry.py
│       └── imports: definitions
│
└── examples/
    └── trading_tools.py
        └── imports: tools
```

## 🚀 Usage Examples

### Create Custom Agent
```python
from agents.core import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, scope_id=None):
        super().__init__(
            name="MyAgent",
            system_prompt="Your prompt",
            scope_id=scope_id
        )
```

### Register Custom Tool
```python
from agents.tools import tool_registry, ToolDefinition, ToolParameter

async def my_tool(param: str) -> dict:
    return {"result": param}

tool_registry.register(ToolDefinition(
    name="my_tool",
    description="Tool description",
    parameters=[
        ToolParameter(
            name="param",
            type="string",
            description="Parameter description",
            required=True
        )
    ],
    function=my_tool
))
```

### Use Memory
```python
from agents.memory import ConversationMemory, Message

memory = ConversationMemory()
msg = Message(role="user", content="Hello")
memory.add_message(msg, scope_id="user_1")
messages = memory.get_messages(scope_id="user_1")
```

## 📈 Scalability

### Adding New Agent Type
1. Create file in `agents/core/`
2. Extend `BaseAgent`
3. Export in `agents/core/__init__.py`
4. Export in `agents/__init__.py`

### Adding New Tool Category
1. Create file in `agents/examples/` or new subfolder
2. Define tool functions
3. Register tools
4. Export registration function

### Adding New Feature
1. Create new subfolder in `agents/`
2. Implement feature
3. Create `__init__.py` with exports
4. Export in main `agents/__init__.py`

## 🔧 Maintenance

### File Organization Rules
- One feature per subfolder
- One class/function group per file
- Clear `__init__.py` exports
- Minimal cross-module dependencies

### Import Rules
- Import from submodules, not from files
- Use main `agents/__init__.py` for public API
- Keep internal imports within submodules

### Testing
- Test each module independently
- Test integration between modules
- Use `test_setup.py` for verification

## 📝 Adding New Module

### Step 1: Create Folder
```bash
mkdir agents/new_feature
```

### Step 2: Create Files
```
agents/new_feature/
├── __init__.py
└── implementation.py
```

### Step 3: Implement Feature
```python
# agents/new_feature/implementation.py
class NewFeature:
    pass
```

### Step 4: Export in Submodule
```python
# agents/new_feature/__init__.py
from .implementation import NewFeature
__all__ = ["NewFeature"]
```

### Step 5: Export in Main Module
```python
# agents/__init__.py
from agents.new_feature import NewFeature
__all__ = [..., "NewFeature"]
```

## 🎯 Best Practices

1. **Keep modules focused** - One responsibility per module
2. **Clear exports** - Use `__all__` in every `__init__.py`
3. **Minimal dependencies** - Reduce cross-module imports
4. **Consistent naming** - Follow Python conventions
5. **Good documentation** - Docstrings for all classes/functions
6. **Type hints** - Use type hints for clarity
7. **Error handling** - Handle errors gracefully
8. **Testing** - Test each module independently

---

**Last Updated**: 2026-04-14
**Version**: 1.0.0
