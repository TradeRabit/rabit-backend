# Trading Tools Summary

## 📋 Overview

Rabit Agent memiliki sistem tools yang terintegrasi dengan WebSocket untuk mendapatkan data real-time. Tools dirancang dengan error handling yang sangat informatif untuk AI.

## 🛠️ Available Tools

### 1. get_price

**Description:** Get real-time market price for a trading symbol from WebSocket data.

**Parameters:**
- `symbol` (string, required): Trading symbol (e.g., SOL, BTC, ETH)

**Returns:**
```json
{
  "success": true,
  "symbol": "SOL",
  "price": 145.67,
  "change_24h": 5.23,
  "volume_24h": 1234567890.50,
  "high_24h": 148.90,
  "low_24h": 142.30,
  "market_cap": 65000000000.0,
  "fdv": 70000000000.0,
  "open_interest": 500000000.0,
  "funding_rate": 0.0001,
  "timestamp": "2026-04-14T10:30:00Z"
}
```

**Supported Symbols:** BTC, ETH, SOL, DOGE, BNB, SUI, APT, ARB, RENDER, XRP, INJ, LINK, PYTH, JTO, AVAX, WIF, JUP, TAO, KMNO, TNSR, DRIFT, RAY, HYPE, LTC, FARTCOIN

**Documentation:** [GET_PRICE_TOOL.md](./GET_PRICE_TOOL.md)

## 🎯 Error Handling

### Informative Errors for AI

Sistem error handling dirancang khusus agar AI dapat memahami dan memperbaiki kesalahan tanpa intervensi manusia.

### Error Types

#### 1. Missing Required Parameter

**Scenario:** AI lupa memberikan parameter yang required

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid parameters provided",
  "error_details": {
    "validation_errors": [
      {
        "parameter": "symbol",
        "error": "Required parameter missing",
        "type": "string",
        "description": "Trading symbol in uppercase (e.g., SOL, BTC, ETH...)"
      }
    ],
    "expected_parameters": [
      {
        "name": "symbol",
        "type": "string",
        "required": true,
        "description": "Trading symbol in uppercase..."
      }
    ],
    "provided_parameters": [],
    "suggestion": "Check parameter names, types, and required fields"
  }
}
```

**What AI Learns:**
- ✅ Which parameter is missing
- ✅ What type it should be
- ✅ What the parameter is for
- ✅ How to fix the error

#### 2. Wrong Parameter Name

**Scenario:** AI menggunakan nama parameter yang salah (e.g., 'ticker' instead of 'symbol')

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid parameters provided",
  "error_details": {
    "validation_errors": [
      {
        "parameter": "ticker",
        "error": "Unexpected parameter",
        "suggestion": "Expected parameters: symbol"
      },
      {
        "parameter": "symbol",
        "error": "Required parameter missing",
        "type": "string"
      }
    ],
    "expected_parameters": [...],
    "provided_parameters": ["ticker"],
    "suggestion": "Check parameter names, types, and required fields"
  }
}
```

**What AI Learns:**
- ✅ The parameter name is wrong
- ✅ What the correct parameter name should be
- ✅ What parameters were actually provided

#### 3. Tool Not Found

**Scenario:** AI mencoba memanggil tool yang tidak ada

**Error Response:**
```json
{
  "success": false,
  "error": "Tool 'get_market_data' not found",
  "error_details": {
    "available_tools": ["get_price"],
    "suggestion": "Check available tools and use the correct tool name"
  }
}
```

**What AI Learns:**
- ✅ The tool doesn't exist
- ✅ What tools are available
- ✅ How to check available tools

#### 4. Data Not Available

**Scenario:** Symbol valid tapi data belum tersedia dari WebSocket

**Error Response:**
```json
{
  "success": false,
  "error": "Price data not available for INVALID",
  "symbol": "INVALID",
  "suggestion": "Make sure WebSocket is connected and symbol is valid. Available symbols: BTC, ETH, SOL..."
}
```

**What AI Learns:**
- ✅ Data is not available
- ✅ What symbols are supported
- ✅ Possible reasons (WebSocket not connected)

## 🔄 Error Flow

```
AI calls tool with wrong params
         ↓
Tool Registry validates parameters
         ↓
Validation fails
         ↓
Detailed error generated
         ↓
Error formatted for AI
         ↓
AI receives informative error
         ↓
AI understands and fixes
         ↓
AI retries with correct params
         ↓
Success!
```

## 📊 Error Message Structure

Every error message includes:

1. **Clear Error Description**
   - What went wrong in simple terms

2. **Validation Errors**
   - Specific parameter issues
   - Expected types and descriptions

3. **Expected Parameters**
   - Complete list of parameters
   - Types and requirements
   - Descriptions

4. **Provided Parameters**
   - What AI actually sent
   - For comparison with expected

5. **Helpful Suggestions**
   - How to fix the error
   - What to check

## 🎓 AI Learning Examples

### Example 1: AI Learns from Missing Parameter

**First Attempt:**
```python
# AI calls without parameter
await tool_registry.execute("get_price", {})
```

**Error Received:**
```
Tool execution failed: Invalid parameters provided

Parameter Validation Errors:
  - symbol: Required parameter missing
    Expected: Trading symbol in uppercase (e.g., SOL, BTC, ETH...)

Expected Parameters:
  - symbol (string, REQUIRED)
    Trading symbol in uppercase...

Provided Parameters: []

Suggestion: Check parameter names, types, and required fields
```

**AI Understands:**
- "I need to provide 'symbol' parameter"
- "It should be a string"
- "It should be uppercase"
- "Examples: SOL, BTC, ETH"

**Second Attempt:**
```python
# AI fixes and retries
await tool_registry.execute("get_price", {"symbol": "SOL"})
# ✅ Success!
```

### Example 2: AI Learns from Wrong Parameter Name

**First Attempt:**
```python
# AI uses wrong parameter name
await tool_registry.execute("get_price", {"ticker": "SOL"})
```

**Error Received:**
```
Tool execution failed: Invalid parameters provided

Parameter Validation Errors:
  - ticker: Unexpected parameter
    Expected parameters: symbol
  - symbol: Required parameter missing

Expected Parameters:
  - symbol (string, REQUIRED)

Provided Parameters: ['ticker']
```

**AI Understands:**
- "I used 'ticker' but it should be 'symbol'"
- "The correct parameter name is 'symbol'"

**Second Attempt:**
```python
# AI fixes parameter name
await tool_registry.execute("get_price", {"symbol": "SOL"})
# ✅ Success!
```

## 🚀 Benefits

### For AI
- ✅ Self-correcting without human intervention
- ✅ Learns from detailed error messages
- ✅ Understands what went wrong and how to fix
- ✅ Can retry with correct parameters

### For Developers
- ✅ Less debugging needed
- ✅ AI handles errors gracefully
- ✅ Comprehensive error logs
- ✅ Easy to add new tools

### For Users
- ✅ Seamless experience
- ✅ AI fixes errors automatically
- ✅ No need to understand technical details
- ✅ Fast and reliable responses

## 📝 Adding New Tools

When adding new tools, follow this pattern for error handling:

```python
async def my_tool(param1: str, param2: int) -> dict:
    """
    Tool description
    
    Args:
        param1: Parameter 1 description
        param2: Parameter 2 description
        
    Returns:
        Result data
    """
    # Validate inputs
    if not param1:
        return {
            "success": False,
            "error": "param1 cannot be empty",
            "suggestion": "Provide a valid param1 value"
        }
    
    # Process
    try:
        result = do_something(param1, param2)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "suggestion": "Check your parameters and try again"
        }

# Register with detailed parameter descriptions
tool_registry.register(ToolDefinition(
    name="my_tool",
    description="Detailed description of what the tool does",
    parameters=[
        ToolParameter(
            name="param1",
            type="string",
            description="Detailed description with examples",
            required=True
        ),
        ToolParameter(
            name="param2",
            type="number",
            description="Detailed description with valid range",
            required=True
        )
    ],
    function=my_tool
))
```

## 🧪 Testing Error Handling

Test file: `test_error_handling.py`

```bash
python test_error_handling.py
```

Tests cover:
- ✅ Missing required parameters
- ✅ Wrong parameter names
- ✅ Tool not found
- ✅ Multiple parameters with validation
- ✅ Error message formatting

## 📚 Related Documentation

- [GET_PRICE_TOOL.md](./GET_PRICE_TOOL.md) - Detailed get_price documentation
- [AGENTS_STRUCTURE.md](./AGENTS_STRUCTURE.md) - Agent system architecture
- [API_REFERENCE.md](./API_REFERENCE.md) - Complete API reference

---

**Last Updated:** 2026-04-14
**Version:** 1.0.0
**Status:** ✅ Production Ready
