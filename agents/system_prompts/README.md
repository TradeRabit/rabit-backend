# System Prompts

This folder contains system prompts for different agent types.

## Available Prompts

### trading_agent.txt
Main trading assistant prompt. Used for general trading assistance, market analysis, and tool usage.

**Use cases:**
- General trading questions
- Market analysis
- Setting up alerts
- Chart analysis

### analysis_agent.txt
Specialized analysis agent prompt. Focused on deep technical and fundamental analysis.

**Use cases:**
- Detailed technical analysis
- Pattern recognition
- Market structure analysis
- Correlation studies

### risk_management.txt
Risk management specialist prompt. Focused on capital preservation and risk assessment.

**Use cases:**
- Position sizing
- Stop-loss recommendations
- Portfolio risk assessment
- Risk/reward calculations

## Usage

```python
from agents import TradingAgent
from agents.system_prompts import get_trading_agent_prompt

# Load prompt directly if you need it
prompt = get_trading_agent_prompt()

# TradingAgent already loads trading_agent.txt by default
agent = TradingAgent(scope_id="user_123")
```

## Adding New Prompts

1. Create new `.txt` file in this folder
2. Add loader function in `__init__.py`
3. Use that loader from the corresponding agent class or factory
4. Update this README

## Best Practices

- Keep prompts focused and specific
- Use clear, actionable language
- Include examples where helpful
- Update prompts based on agent performance
- Version control prompt changes
- Keep prompts in plain text unless you truly need dynamic prompt generation in Python
