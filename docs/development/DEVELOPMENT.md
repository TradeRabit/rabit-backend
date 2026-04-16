# Development Guide

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- pip
- Virtual environment tool
- Git
- (Optional) Docker & Docker Compose

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd rabit-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run tests
python test_setup.py

# Run application
python main.py
```

## 📁 Project Structure

```
rabit-backend/
├── agents/              # Agent implementations
│   ├── base.py         # BaseAgent class
│   ├── memory.py       # Memory management
│   ├── compression.py  # Auto compression
│   ├── tools.py        # Tool system
│   ├── example_tools.py # Example tools
│   └── trading_agent.py # Trading agent
├── config/             # Configuration
│   └── settings.py     # Settings management
├── models/             # Data models
│   └── base.py         # Base Pydantic models
├── utils/              # Utilities
│   └── logger.py       # Logging
├── ws/                 # WebSocket (TODO)
│   └── client.py       # Drift client
└── main.py             # Entry point
```

## 🔧 Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Implement Feature

Follow the coding standards below.

### 3. Test Your Changes

```bash
# Run existing tests
python test_setup.py

# Add new tests if needed
# TODO: Add pytest tests
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: your feature description"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

## 📝 Coding Standards

### Python Style Guide

Follow PEP 8 with these additions:

```python
# Use type hints
def function_name(param: str, optional: Optional[int] = None) -> dict:
    """
    Function description
    
    Args:
        param: Parameter description
        optional: Optional parameter description
        
    Returns:
        Return value description
    """
    return {"result": "value"}

# Use async/await for I/O operations
async def async_function() -> str:
    result = await some_async_operation()
    return result

# Use Pydantic for data models
from pydantic import BaseModel

class MyModel(BaseModel):
    field1: str
    field2: int
    field3: Optional[str] = None
```

### Naming Conventions

```python
# Classes: PascalCase
class MyAgent(BaseAgent):
    pass

# Functions/Methods: snake_case
def process_message(message: str) -> str:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_TOKENS = 4000

# Private methods: _leading_underscore
def _internal_method(self):
    pass
```

### Documentation

```python
# Module docstring
"""Module description"""

# Class docstring
class MyClass:
    """
    Class description
    
    Attributes:
        attr1: Attribute description
        attr2: Attribute description
    """
    
    def method(self, param: str) -> str:
        """
        Method description
        
        Args:
            param: Parameter description
            
        Returns:
            Return value description
            
        Raises:
            ValueError: When something goes wrong
        """
        pass
```

## 🛠️ Common Development Tasks

### Adding a New Agent

```python
# 1. Create new file in agents/
# agents/my_agent.py

from .base import BaseAgent
from typing import Optional

class MyAgent(BaseAgent):
    """My custom agent"""
    
    def __init__(self, scope_id: Optional[str] = None):
        super().__init__(
            name="MyAgent",
            system_prompt="Your system prompt",
            scope_id=scope_id
        )
    
    async def process_query(self, query: str) -> str:
        """Process query with tools"""
        return await self.process(query, use_tools=True)

# 2. Export in agents/__init__.py
from .my_agent import MyAgent
__all__ = [..., "MyAgent"]

# 3. Use in main.py or other files
from agents.my_agent import MyAgent

agent = MyAgent(scope_id="user_123")
response = await agent.process_query("Hello")
```

### Adding a New Tool

```python
# 1. Define tool function
async def my_tool(param1: str, param2: int = 0) -> dict:
    """
    Tool description
    
    Args:
        param1: Parameter 1 description
        param2: Parameter 2 description
        
    Returns:
        Result dictionary
    """
    # Implementation
    return {"result": "success"}

# 2. Register tool
from agents.tools import tool_registry, ToolDefinition, ToolParameter

tool_registry.register(ToolDefinition(
    name="my_tool",
    description="Tool description for agent",
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

# 3. Use in agent
response = await agent.process(
    "Use my_tool with param1='test'",
    use_tools=True
)
```

### Adding Configuration

```python
# 1. Add to .env.example
NEW_CONFIG_VALUE=default_value

# 2. Add to config/settings.py
class Settings:
    # ... existing settings ...
    NEW_CONFIG_VALUE = os.getenv("NEW_CONFIG_VALUE", "default")

# 3. Use in code
from config.settings import settings

value = settings.NEW_CONFIG_VALUE
```

### Adding a Model

```python
# 1. Create in models/
# models/my_model.py

from .base import BaseModel
from typing import Optional

class MyModel(BaseModel):
    """My data model"""
    
    field1: str
    field2: int
    field3: Optional[str] = None

# 2. Export in models/__init__.py
from .my_model import MyModel
__all__ = [..., "MyModel"]

# 3. Use in code
from models.my_model import MyModel

data = MyModel(field1="value", field2=123)
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python test_setup.py

# TODO: Add pytest
# pytest tests/
# pytest tests/test_agents.py
# pytest tests/test_tools.py -v
```

### Writing Tests

```python
# TODO: Add pytest tests
# tests/test_my_feature.py

import pytest
from agents.my_agent import MyAgent

@pytest.mark.asyncio
async def test_my_agent():
    agent = MyAgent(scope_id="test")
    response = await agent.process_query("test")
    assert response is not None

def test_my_function():
    result = my_function("input")
    assert result == "expected"
```

## 🐛 Debugging

### Enable Debug Logging

```bash
# In .env
DEBUG=true
```

### Using Logger

```python
from utils.logger import get_logger

logger = get_logger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Common Issues

#### 1. Import Errors

```bash
# Make sure virtual environment is activated
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. API Key Issues

```bash
# Check .env file exists
ls -la .env

# Check API key is set
cat .env | grep ANTHROPIC_API_KEY
```

#### 3. Module Not Found

```bash
# Make sure you're in the right directory
pwd  # Should be in rabit-backend/

# Check Python path
python -c "import sys; print(sys.path)"
```

## 🔍 Code Review Checklist

Before submitting PR:

- [ ] Code follows style guide
- [ ] All functions have docstrings
- [ ] Type hints are used
- [ ] Tests are added/updated
- [ ] Documentation is updated
- [ ] No sensitive data in code
- [ ] Error handling is proper
- [ ] Logging is appropriate
- [ ] Code is DRY (Don't Repeat Yourself)
- [ ] No commented-out code

## 📚 Resources

### Internal Documentation
- [../README.md](../README.md) - Main documentation
- [FEATURES.md](FEATURES.md) - Feature documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [API_REFERENCE.md](API_REFERENCE.md) - API reference
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture overview

### External Resources
- [Anthropic API Docs](https://docs.anthropic.com/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Python Async/Await](https://docs.python.org/3/library/asyncio.html)
- [PEP 8 Style Guide](https://pep8.org/)

## 🤝 Contributing

### Contribution Process

1. Fork the repository
2. Create feature branch
3. Implement feature
4. Add tests
5. Update documentation
6. Submit pull request

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

**Examples:**
```
feat: add auto conversation compression

Implement automatic compression when token limit is reached.
Includes summarization and fallback truncation.

Closes #123
```

```
fix: handle missing tool parameters

Add validation for required parameters and provide
detailed error messages to agent.
```

## 🎯 Development Roadmap

### Phase 1: Core Features (✅ Complete)
- [x] Agent system
- [x] Memory management
- [x] Auto compression
- [x] Tool system
- [x] Documentation

### Phase 2: WebSocket Integration (🚧 In Progress)
- [ ] Drift WebSocket client
- [ ] WebSocket server
- [ ] Real-time data streaming

### Phase 3: Trading Features
- [ ] Real market data
- [ ] Order placement
- [ ] Position management
- [ ] Risk management

### Phase 4: Production Ready
- [ ] Database integration
- [ ] Authentication
- [ ] Monitoring
- [ ] Deployment

## 💡 Tips & Best Practices

### 1. Use Virtual Environment
Always activate virtual environment before working.

### 2. Keep Dependencies Updated
Regularly update dependencies for security.

### 3. Write Tests
Test your code before committing.

### 4. Document Your Code
Good documentation saves time later.

### 5. Use Type Hints
Type hints improve code quality and IDE support.

### 6. Handle Errors Gracefully
Always handle potential errors.

### 7. Log Appropriately
Use appropriate log levels.

### 8. Keep Functions Small
Small, focused functions are easier to test and maintain.

### 9. Use Async/Await
Use async for I/O operations.

### 10. Review Your Own Code
Review your code before submitting PR.

---

**Last Updated**: 2026-04-14
**Version**: 1.0.0
