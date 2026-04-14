# Quick Start Guide

## 🚀 Setup dalam 5 Menit

### 1. Clone & Setup

```bash
cd rabit-backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy .env.example
cp .env.example .env
```

Edit `.env` dan tambahkan API key:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Test Setup

```bash
python test_setup.py
```

Output yang diharapkan:
```
✅ Memory test passed
✅ Compression test passed
✅ Tool registry test passed
✅ Tool execution test passed
✅ All tests passed!
```

### 4. Run Application

```bash
python main.py
```

## 📝 Example: Create Simple Agent

```python
# my_agent.py
import asyncio
from agents.base import BaseAgent
from agents.example_tools import register_example_tools

async def main():
    # Register tools
    register_example_tools()
    
    # Create agent
    agent = BaseAgent(
        name="MyAgent",
        system_prompt="You are a helpful assistant",
        scope_id="user_123"
    )
    
    # Process query
    response = await agent.process(
        "What's the price of SOL?",
        use_tools=True
    )
    
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🛠️ Example: Create Custom Tool

```python
# custom_tool.py
from agents.tools import tool_registry, ToolDefinition, ToolParameter

async def get_weather(city: str) -> dict:
    """Get weather for a city"""
    return {
        "city": city,
        "temperature": 25,
        "condition": "Sunny"
    }

# Register tool
tool_registry.register(ToolDefinition(
    name="get_weather",
    description="Get current weather for a city",
    parameters=[
        ToolParameter(
            name="city",
            type="string",
            description="City name",
            required=True
        )
    ],
    function=get_weather
))
```

## 🎯 Example: Use Memory Scopes

```python
from agents.trading_agent import TradingAgent

# Create agent for user 1
agent1 = TradingAgent(scope_id="user_1")
await agent1.process_trading_query("What's SOL price?")

# Create agent for user 2 (different memory)
agent2 = TradingAgent(scope_id="user_2")
await agent2.process_trading_query("What's BTC price?")

# Each agent has isolated memory
```

## 🔍 Example: Test Error Handling

```python
from agents.tools import tool_registry
from agents.example_tools import register_example_tools

register_example_tools()

# Test with missing parameter
result = await tool_registry.execute(
    "get_market_price",
    {"market": "drift"}  # Missing 'symbol'
)

print(f"Success: {result.success}")
print(f"Error: {result.error}")
print(f"Details: {result.error_details}")
```

Output:
```
Success: False
Error: Invalid parameters provided
Details: {
    'validation_errors': [
        {
            'parameter': 'symbol',
            'error': 'Required parameter missing',
            'type': 'string',
            'description': 'Trading symbol (e.g., SOL, BTC, ETH)'
        }
    ],
    'expected_parameters': [...],
    'provided_parameters': ['market'],
    'suggestion': 'Check parameter names, types, and required fields'
}
```

## 📚 Next Steps

1. Baca [FEATURES.md](FEATURES.md) untuk dokumentasi lengkap
2. Lihat [agents/example_tools.py](agents/example_tools.py) untuk contoh tools
3. Lihat [agents/trading_agent.py](agents/trading_agent.py) untuk contoh agent
4. Implement Drift WebSocket client di [ws/client.py](ws/client.py)

## 🐛 Troubleshooting

### Import Error

```bash
# Make sure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### Missing API Key

```bash
# Check .env file
cat .env  # Linux/Mac
type .env  # Windows

# Make sure ANTHROPIC_API_KEY is set
```

### Module Not Found

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## 💡 Tips

1. **Memory Management**: Gunakan `scope_id` untuk isolate memory per user
2. **Auto Compression**: Set `max_tokens` di BaseAgent constructor
3. **Tool Errors**: Baca error_details untuk debug parameter issues
4. **Logging**: Set `DEBUG=true` di .env untuk detailed logs
