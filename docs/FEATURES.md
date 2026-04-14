# Rabit Backend - Features

## 🤖 Agent Features

### 1. Auto Conversation Compression

Otomatis compress conversation history ketika mencapai token limit.

**Cara Kerja:**
- Monitor token count di setiap conversation
- Ketika melebihi `max_tokens` (default: 4000), otomatis compress
- Menyimpan system message dan recent messages
- Summarize middle messages menggunakan Claude
- Fallback ke truncation jika compression gagal

**Usage:**
```python
from agents.trading_agent import TradingAgent

agent = TradingAgent(scope_id="user_123")
# Auto-compression akan berjalan otomatis
response = await agent.process_trading_query("Your query here")
```

### 2. Memory Management (Scoped & Global)

Memory system dengan support untuk scope by ID dan global memory.

**Features:**
- **Scoped Memory**: Memory per user/session dengan `scope_id`
- **Global Memory**: Shared memory tanpa scope
- **Message History**: Menyimpan semua messages dengan timestamp
- **Memory Operations**: Add, get, clear, list scopes

**Usage:**
```python
from agents.memory import ConversationMemory, Message

# Create memory
memory = ConversationMemory()

# Add to scoped memory
message = Message(role="user", content="Hello")
memory.add_message(message, scope_id="user_123")

# Add to global memory
memory.add_message(message)

# Get messages
scoped_messages = memory.get_messages(scope_id="user_123", limit=10)
global_messages = memory.get_messages()

# Clear
memory.clear_scope("user_123")
memory.clear_global()
```

### 3. Tool Calling System

Comprehensive tool system dengan detailed error handling.

**Features:**
- **Tool Registry**: Central registry untuk semua tools
- **Schema Validation**: Automatic parameter validation
- **Detailed Errors**: Error messages yang jelas untuk agent
- **Type Checking**: Validate parameter types
- **Missing Parameters**: Detect dan explain missing required params

**Tool Definition:**
```python
from agents.tools import tool_registry, ToolDefinition, ToolParameter

async def my_tool(param1: str, param2: int) -> dict:
    return {"result": "success"}

tool_registry.register(ToolDefinition(
    name="my_tool",
    description="Tool description",
    parameters=[
        ToolParameter(
            name="param1",
            type="string",
            description="Parameter 1 description",
            required=True
        ),
        ToolParameter(
            name="param2",
            type="number",
            description="Parameter 2 description",
            required=False,
            default=0
        )
    ],
    function=my_tool
))
```

### 4. Detailed Error Messages

Ketika tool call gagal, agent mendapat error message yang sangat detail:

**Error Information:**
- ✅ Tool name yang dipanggil
- ✅ Validation errors dengan detail per parameter
- ✅ Expected parameters dengan type dan description
- ✅ Provided parameters yang agent kirim
- ✅ Suggestion untuk fix error
- ✅ Error type (TypeError, ValidationError, etc)

**Example Error Output:**
```
Tool execution failed: Invalid parameters provided

Details:

Parameter Validation Errors:
  - user_id: Required parameter missing
    Expected: User ID to fetch account information

Expected Parameters:
  - user_id (string, required): User ID to fetch account information

You provided: symbol, market

Suggestion: Check parameter names, types, and required fields
```

## 📁 Project Structure

```
rabit-backend/
├── agents/
│   ├── base.py              # BaseAgent dengan compression & memory
│   ├── memory.py            # Memory management (scoped & global)
│   ├── compression.py       # Auto conversation compression
│   ├── tools.py             # Tool registry & error handling
│   ├── example_tools.py     # Example tools
│   └── trading_agent.py     # Trading agent implementation
├── config/
│   └── settings.py          # Configuration
├── models/
│   └── base.py              # Pydantic models
├── utils/
│   └── logger.py            # Logging utility
├── ws/
│   └── client.py            # Drift WebSocket client (TODO)
└── main.py                  # Entry point with tests
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup .env
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Run Tests

```bash
python main.py
```

### 3. Create Custom Agent

```python
from agents.base import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, scope_id=None):
        super().__init__(
            name="MyAgent",
            system_prompt="Your system prompt here",
            scope_id=scope_id,
            max_tokens=4000
        )
    
    async def process_query(self, query: str) -> str:
        return await self.process(query, use_tools=True)
```

### 4. Register Custom Tools

```python
from agents.tools import tool_registry, ToolDefinition, ToolParameter

async def my_custom_tool(param: str) -> dict:
    return {"result": param}

tool_registry.register(ToolDefinition(
    name="my_custom_tool",
    description="My custom tool",
    parameters=[
        ToolParameter(
            name="param",
            type="string",
            description="Parameter description",
            required=True
        )
    ],
    function=my_custom_tool
))
```

## 🔧 Configuration

Edit `.env` file:

```env
# Claude API
ANTHROPIC_API_KEY=your_api_key_here

# Drift Protocol
DRIFT_RPC_URL=https://api.mainnet-beta.solana.com
DRIFT_PROGRAM_ID=dRiftyHA39MWEi3m9aunc5MzRF1JYJjb5ciH7N27eNn

# WebSocket
WS_HOST=0.0.0.0
WS_PORT=8000

# Environment
ENVIRONMENT=development
DEBUG=true
```

## 📝 Example Tools

Sudah include 3 example tools:

1. **get_market_price**: Get market price untuk symbol
2. **calculate_position_size**: Calculate position size dengan risk management
3. **get_account_info**: Get user account information

## 🎯 Next Steps

- [ ] Implement Drift WebSocket client
- [ ] Add more trading tools
- [ ] Implement WebSocket server untuk client connections
- [ ] Add authentication & authorization
- [ ] Add database for persistent storage
- [ ] Add monitoring & metrics
