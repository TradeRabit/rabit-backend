# Test Suite

Organized test structure for Rabit Backend.

## Directory Structure

```
test/
├── ws/                    # WebSocket Tests
│   ├── test_backpack.py   - Backpack Exchange WebSocket client
│   ├── test_drift.py      - Drift Protocol WebSocket client
│   ├── test_drift_mock.py - Drift mock tests
│   ├── test_ws.py         - General WebSocket tests
│   └── ws_example.py      - WebSocket usage examples
│
├── database/              # Database Tests
│   ├── test_ohlc_database.py - OHLC historical data database
│   └── test_coingecko.py     - CoinGecko integration & database
│
├── tools/                 # Tool Tests
│   ├── test_get_price_tool.py - Price fetching tool
│   ├── test_news_tools.py     - News monitoring tools
│   └── test_web_search.py     - Web search functionality
│
├── utils/                 # Utility Tests
│   ├── test_categories.py - Crypto category utilities
│   └── test_intervals.py  - Timeframe/interval utilities
│
├── news/                  # News Tests
│   ├── test_regex_news.py    - Regex-based news filtering
│   ├── test_quick_regex.py   - Quick regex tests
│   └── test_specific_news.py - Specific news source tests
│
└── integration/           # Integration Tests
    ├── test_error_handling.py - Error handling tests
    └── test_setup.py          - Setup and configuration tests
```

## Running Tests

### Run All Tests
```bash
# From project root
python -m pytest test/

# With coverage
python -m pytest test/ --cov=. --cov-report=html
```

### Run Specific Test Category
```bash
# WebSocket tests
python -m pytest test/ws/

# Database tests
python -m pytest test/database/

# Tool tests
python -m pytest test/tools/

# Utility tests
python -m pytest test/utils/

# News tests
python -m pytest test/news/

# Integration tests
python -m pytest test/integration/
```

### Run Individual Test File
```bash
# Run specific test
python test/utils/test_categories.py

# Or with pytest
python -m pytest test/utils/test_categories.py -v
```

### Run with PYTHONPATH (Windows)
```powershell
$env:PYTHONPATH="$PWD"; python test/utils/test_categories.py
```

```bash
# Linux/Mac
PYTHONPATH=. python test/utils/test_categories.py
```

## Test Categories

### WebSocket Tests (`ws/`)
Tests for WebSocket clients connecting to various exchanges and protocols:
- Backpack Exchange integration
- Drift Protocol integration
- General WebSocket functionality
- Mock tests for offline testing

### Database Tests (`database/`)
Tests for data persistence and storage:
- OHLC historical candlestick data
- CoinGecko coin information
- Database operations (CRUD, stats, etc.)

### Tool Tests (`tools/`)
Tests for agent tools and utilities:
- Price fetching from multiple sources
- News monitoring and filtering
- Web search integration

### Utility Tests (`utils/`)
Tests for helper functions and utilities:
- Crypto category normalization (L1, L2, DeFi, AI, etc.)
- Timeframe/interval handling (1m, 5m, 1h, 1d, etc.)

### News Tests (`news/`)
Tests for news monitoring functionality:
- Regex-based filtering
- News source integration
- Sentiment analysis

### Integration Tests (`integration/`)
Tests for system integration and setup:
- Error handling across components
- Configuration and setup validation
- End-to-end workflows

## Writing New Tests

### Test File Naming
- Use `test_*.py` prefix for test files
- Name should describe what's being tested
- Place in appropriate subdirectory

### Test Function Naming
- Use `test_*` prefix for test functions
- Use descriptive names: `test_normalize_category()`, `test_get_price_from_phantom_futures()`

### Example Test Structure
```python
"""Test description"""
import pytest
from module import function_to_test


def test_basic_functionality():
    """Test basic functionality"""
    result = function_to_test()
    assert result == expected_value


def test_edge_cases():
    """Test edge cases"""
    with pytest.raises(ValueError):
        function_to_test(invalid_input)


async def test_async_function():
    """Test async function"""
    result = await async_function()
    assert result is not None
```

## Test Requirements

Install test dependencies:
```bash
pip install pytest pytest-asyncio pytest-cov
```

## CI/CD Integration

Tests are automatically run on:
- Pull requests
- Commits to main branch
- Scheduled daily runs

## Coverage

Generate coverage report:
```bash
python -m pytest test/ --cov=. --cov-report=html
open htmlcov/index.html
```

## Notes

- All tests should be independent and not rely on external state
- Use mocks for external API calls when possible
- Clean up test data after tests complete
- Add docstrings to explain what each test validates
