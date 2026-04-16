# API Reference

## Agent Classes

### BaseAgent

Base class untuk semua agents dengan memory, compression, dan tool support.

```python
from agents.base import BaseAgent

agent = BaseAgent(
    name="MyAgent",
    system_prompt="You are a helpful assistant",
    scope_id="user_123",  # Optional
    max_tokens=4000,      # Optional
    model="claude-3-5-sonnet-20241022"  # Optional
)
```

**Parameters:**
- `name` (str): Agent name
- `system_prompt` (str): System prompt untuk agent
- `scope_id` (str, optional): Scope ID untuk memory isolation
- `max_tokens` (int, optional): Max tokens sebelum auto-compression (default: 4000)
- `model` (str, optional): Claude model name (default: claude-3-5-sonnet-20241022)

**Methods:**

#### `add_message(role: str, content: str)`
Add message ke conversation history.

```python
agent.add_message("user", "Hello")
agent.add_message("assistant", "Hi there!")
```

#### `get_conversation_history(limit: Optional[int] = None) -> List[Dict]`
Get conversation history.

```python
history = agent.get_conversation_history(limit=10)
```

#### `clear_history()`
Clear conversation history.

```python
agent.clear_history()
```

#### `async process(user_input: str, use_tools: bool = False) -> str`
Process user input dan return response.

```python
response = await agent.process("What's the weather?", use_tools=True)
```

---

## Memory Classes

### ConversationMemory

Manage conversation memory dengan scoped dan global support.

```python
from agents.memory import ConversationMemory, Message

memory = ConversationMemory()
```

**Methods:**

#### `add_message(message: Message, scope_id: Optional[str] = None)`
Add message ke memory.

```python
msg = Message(role="user", content="Hello")
memory.add_message(msg, scope_id="user_123")
```

#### `get_messages(scope_id: Optional[str] = None, limit: Optional[int] = None) -> List[Message]`
Get messages dari memory.

```python
messages = memory.get_messages(scope_id="user_123", limit=10)
```

#### `clear_scope(scope_id: str)`
Clear scoped memory.

```python
memory.clear_scope("user_123")
```

#### `clear_global()`
Clear global memory.

```python
memory.clear_global()
```

#### `get_all_scopes() -> List[str]`
Get all scope IDs.

```python
scopes = memory.get_all_scopes()
```

---

## Compression Classes

### ConversationCompressor

Auto-compress conversation history.

```python
from agents.compression import ConversationCompressor

compressor = ConversationCompressor(
    max_tokens=4000,
    model="claude-3-5-sonnet-20241022"
)
```

**Methods:**

#### `count_tokens(messages: List[Dict]) -> int`
Count tokens dalam messages.

```python
token_count = compressor.count_tokens(messages)
```

#### `needs_compression(messages: List[Dict]) -> bool`
Check if compression needed.

```python
if compressor.needs_compression(messages):
    messages = await compressor.compress(messages)
```

#### `async compress(messages: List[Dict]) -> List[Dict]`
Compress conversation history.

```python
compressed = await compressor.compress(messages)
```

---

## Tool Classes

### ToolRegistry

Central registry untuk tools.

```python
from agents.tools import tool_registry
```

**Methods:**

#### `register(tool: ToolDefinition)`
Register a tool.

```python
tool_registry.register(ToolDefinition(
    name="my_tool",
    description="Tool description",
    parameters=[...],
    function=my_function
))
```

#### `get_tool(name: str) -> Optional[ToolDefinition]`
Get tool by name.

```python
tool = tool_registry.get_tool("my_tool")
```

#### `list_tools() -> List[ToolDefinition]`
List all tools.

```python
tools = tool_registry.list_tools()
```

#### `get_tools_schema() -> List[Dict]`
Get tools schema untuk Claude API.

```python
schema = tool_registry.get_tools_schema()
```

#### `async execute(name: str, arguments: Dict) -> ToolResult`
Execute a tool.

```python
result = await tool_registry.execute("my_tool", {"param": "value"})
```

---

### ToolDefinition

Define a tool.

```python
from agents.tools import ToolDefinition, ToolParameter

tool = ToolDefinition(
    name="get_weather",
    description="Get weather for a city",
    parameters=[
        ToolParameter(
            name="city",
            type="string",
            description="City name",
            required=True
        ),
        ToolParameter(
            name="units",
            type="string",
            description="Temperature units (celsius/fahrenheit)",
            required=False,
            default="celsius"
        )
    ],
    function=get_weather_function
)
```

---

### ToolParameter

Define tool parameter.

```python
from agents.tools import ToolParameter

param = ToolParameter(
    name="city",
    type="string",  # string, number, boolean, array, object
    description="City name",
    required=True,
    default=None  # Optional default value
)
```

---

### ToolResult

Tool execution result.

```python
class ToolResult:
    success: bool
    data: Optional[Any]
    error: Optional[str]
    error_details: Optional[Dict]
```

**Example:**
```python
result = await tool_registry.execute("my_tool", {"param": "value"})

if result.success:
    print(f"Data: {result.data}")
else:
    print(f"Error: {result.error}")
    print(f"Details: {result.error_details}")
```

---

## Example Tools

### get_market_price

Get market price untuk trading symbol.

```python
result = await tool_registry.execute(
    "get_market_price",
    {
        "symbol": "SOL",
        "market": "drift"  # Optional
    }
)
```

**Parameters:**
- `symbol` (string, required): Trading symbol (e.g., SOL, BTC, ETH)
- `market` (string, optional): Market name (default: drift)

**Returns:**
```json
{
    "symbol": "SOL",
    "market": "drift",
    "price": 100.50,
    "timestamp": "2024-01-01T00:00:00Z"
}
```

---

### calculate_position_size

Calculate position size dengan risk management.

```python
result = await tool_registry.execute(
    "calculate_position_size",
    {
        "account_balance": 10000.0,
        "risk_percentage": 2.0,
        "entry_price": 100.0,
        "stop_loss_price": 95.0
    }
)
```

**Parameters:**
- `account_balance` (number, required): Total account balance in USD
- `risk_percentage` (number, required): Risk percentage per trade (e.g., 2.0 for 2%)
- `entry_price` (number, required): Planned entry price
- `stop_loss_price` (number, required): Stop loss price

**Returns:**
```json
{
    "account_balance": 10000.0,
    "risk_percentage": 2.0,
    "risk_amount": 200.0,
    "entry_price": 100.0,
    "stop_loss_price": 95.0,
    "position_size": 40.0,
    "total_cost": 4000.0
}
```

---

### get_account_info

Get user account information.

```python
result = await tool_registry.execute(
    "get_account_info",
    {
        "user_id": "user_123"
    }
)
```

**Parameters:**
- `user_id` (string, required): User ID to fetch account information

**Returns:**
```json
{
    "user_id": "user_123",
    "balance": 1000.0,
    "positions": [],
    "pnl": 0.0
}
```

---

## Error Handling

### Tool Execution Errors

Ketika tool execution gagal, `ToolResult` akan contain detailed error information:

```python
result = await tool_registry.execute("my_tool", {"wrong": "params"})

if not result.success:
    print(f"Error: {result.error}")
    
    # Detailed error information
    if result.error_details:
        # Validation errors
        if "validation_errors" in result.error_details:
            for err in result.error_details["validation_errors"]:
                print(f"Parameter: {err['parameter']}")
                print(f"Error: {err['error']}")
                print(f"Description: {err['description']}")
        
        # Expected parameters
        if "expected_parameters" in result.error_details:
            for param in result.error_details["expected_parameters"]:
                print(f"Name: {param['name']}")
                print(f"Type: {param['type']}")
                print(f"Required: {param['required']}")
        
        # Suggestion
        if "suggestion" in result.error_details:
            print(f"Suggestion: {result.error_details['suggestion']}")
```

### Error Types

1. **Tool Not Found**
   - Error: "Tool 'name' not found"
   - Details: List of available tools

2. **Invalid Parameters**
   - Error: "Invalid parameters provided"
   - Details: Validation errors, expected parameters, provided parameters

3. **Type Error**
   - Error: "Parameter type error"
   - Details: Type mismatch information

4. **Execution Error**
   - Error: "Execution error: {message}"
   - Details: Error type, error message, suggestion

---

## Configuration

### Settings

```python
from config.settings import settings

# Access settings
api_key = settings.ANTHROPIC_API_KEY
rpc_url = settings.DRIFT_RPC_URL
debug = settings.DEBUG
```

**Available Settings:**
- `ANTHROPIC_API_KEY`: Claude API key
- `DRIFT_RPC_URL`: Drift RPC URL
- `DRIFT_PROGRAM_ID`: Drift program ID
- `WS_HOST`: WebSocket host
- `WS_PORT`: WebSocket port
- `ENVIRONMENT`: Environment (development/production)
- `DEBUG`: Debug mode (true/false)

---

## Logging

```python
from utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Info message")
logger.error("Error message")
logger.debug("Debug message")
```

---

## Complete Example

```python
import asyncio
from agents.base import BaseAgent
from agents.tools import tool_registry, ToolDefinition, ToolParameter
from agents.example_tools import register_example_tools

# Define custom tool
async def get_weather(city: str, units: str = "celsius") -> dict:
    return {
        "city": city,
        "temperature": 25,
        "units": units,
        "condition": "Sunny"
    }

# Register custom tool
tool_registry.register(ToolDefinition(
    name="get_weather",
    description="Get weather for a city",
    parameters=[
        ToolParameter(
            name="city",
            type="string",
            description="City name",
            required=True
        ),
        ToolParameter(
            name="units",
            type="string",
            description="Temperature units",
            required=False,
            default="celsius"
        )
    ],
    function=get_weather
))

# Register example tools
register_example_tools()

# Create agent
async def main():
    agent = BaseAgent(
        name="WeatherAgent",
        system_prompt="You are a weather assistant",
        scope_id="user_123"
    )
    
    # Process query
    response = await agent.process(
        "What's the weather in Jakarta?",
        use_tools=True
    )
    
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```
