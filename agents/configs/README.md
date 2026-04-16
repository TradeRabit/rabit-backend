# Agent Configurations

This folder contains JSON configuration files for agents.

## Configuration Files

### trading_agent.json
Main trading agent configuration including model settings, features, and limits.

**Key settings:**
- `model`: Claude model to use
- `temperature`: Response randomness (0-1)
- `features`: Enable/disable features
- `limits`: Resource limits
- `defaults`: Default values

### default_tools.json
Tool configuration including enabled tools, categories, and permissions.

**Sections:**
- `enabled_tools`: List of tools available by default
- `tool_categories`: Tools grouped by function
- `tool_permissions`: Access control for tools

## Usage

```python
from agents.configs import get_trading_agent_config

# Load config
config = get_trading_agent_config()

# Access settings
model = config['model']
temperature = config['temperature']
```

## Customization

You can create custom configurations by:
1. Copying existing config file
2. Modifying settings
3. Loading with `load_config('custom_name')`

## Best Practices

- Keep sensitive data in environment variables
- Version control configuration changes
- Document custom configurations
- Test configuration changes before deployment
