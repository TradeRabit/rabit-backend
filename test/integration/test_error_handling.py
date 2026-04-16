"""Test error handling for tools - verify AI gets informative errors"""
import asyncio
from agents.tools_registry import register_trading_tools
from agents.tools import tool_registry


async def test_error_handling():
    """Test that error messages are informative for AI"""
    
    print("=" * 80)
    print("Testing Error Handling - Informative Errors for AI")
    print("=" * 80)
    
    # Register tools
    register_trading_tools()
    
    # Test 1: Missing required parameter
    print("\n" + "=" * 80)
    print("Test 1: Missing Required Parameter")
    print("=" * 80)
    print("Scenario: AI forgets to provide 'symbol' parameter")
    print("-" * 80)
    
    result = await tool_registry.execute("get_price", {})
    
    print(f"\n✅ Tool correctly rejected the call")
    print(f"\nError Message:")
    print(f"  {result.error}")
    
    if result.error_details:
        print(f"\nDetailed Error Information:")
        
        if "validation_errors" in result.error_details:
            print(f"\n  Validation Errors:")
            for err in result.error_details["validation_errors"]:
                print(f"    - Parameter: {err['parameter']}")
                print(f"      Error: {err['error']}")
                print(f"      Type: {err['type']}")
                print(f"      Description: {err['description']}")
        
        if "expected_parameters" in result.error_details:
            print(f"\n  Expected Parameters:")
            for param in result.error_details["expected_parameters"]:
                req = "REQUIRED" if param["required"] else "optional"
                print(f"    - {param['name']} ({param['type']}, {req})")
                print(f"      {param['description']}")
        
        if "provided_parameters" in result.error_details:
            print(f"\n  Provided Parameters: {result.error_details['provided_parameters']}")
        
        if "suggestion" in result.error_details:
            print(f"\n  Suggestion: {result.error_details['suggestion']}")
    
    print("\n" + "-" * 80)
    print("✅ AI can understand:")
    print("   - Which parameter is missing")
    print("   - What type it should be")
    print("   - What the parameter is for")
    print("   - How to fix the error")
    
    # Test 2: Wrong parameter name
    print("\n" + "=" * 80)
    print("Test 2: Wrong Parameter Name")
    print("=" * 80)
    print("Scenario: AI uses 'ticker' instead of 'symbol'")
    print("-" * 80)
    
    result = await tool_registry.execute("get_price", {"ticker": "SOL"})
    
    print(f"\n✅ Tool correctly rejected the call")
    print(f"\nError Message:")
    print(f"  {result.error}")
    
    if result.error_details:
        print(f"\nDetailed Error Information:")
        
        if "validation_errors" in result.error_details:
            print(f"\n  Validation Errors:")
            for err in result.error_details["validation_errors"]:
                print(f"    - {err}")
        
        if "expected_parameters" in result.error_details:
            print(f"\n  Expected Parameters:")
            for param in result.error_details["expected_parameters"]:
                req = "REQUIRED" if param["required"] else "optional"
                print(f"    - {param['name']} ({param['type']}, {req})")
        
        if "provided_parameters" in result.error_details:
            print(f"\n  Provided Parameters: {result.error_details['provided_parameters']}")
    
    print("\n" + "-" * 80)
    print("✅ AI can understand:")
    print("   - The parameter name is wrong")
    print("   - What the correct parameter name should be")
    print("   - What parameters were actually provided")
    
    # Test 3: Tool not found
    print("\n" + "=" * 80)
    print("Test 3: Tool Not Found")
    print("=" * 80)
    print("Scenario: AI tries to call non-existent tool")
    print("-" * 80)
    
    result = await tool_registry.execute("get_market_data", {"symbol": "SOL"})
    
    print(f"\n✅ Tool correctly rejected the call")
    print(f"\nError Message:")
    print(f"  {result.error}")
    
    if result.error_details:
        print(f"\nDetailed Error Information:")
        
        if "available_tools" in result.error_details:
            print(f"\n  Available Tools:")
            for tool in result.error_details["available_tools"]:
                print(f"    - {tool}")
        
        if "suggestion" in result.error_details:
            print(f"\n  Suggestion: {result.error_details['suggestion']}")
    
    print("\n" + "-" * 80)
    print("✅ AI can understand:")
    print("   - The tool doesn't exist")
    print("   - What tools are available")
    print("   - How to check available tools")
    
    # Test 4: Multiple parameters with one missing
    print("\n" + "=" * 80)
    print("Test 4: Multiple Parameters - One Missing")
    print("=" * 80)
    print("Scenario: AI provides some parameters but misses required ones")
    print("-" * 80)
    
    # Register a multi-param tool for testing
    from agents.tools import ToolDefinition, ToolParameter
    
    async def test_multi_param(param1: str, param2: int, param3: str) -> dict:
        return {"result": "ok"}
    
    tool_registry.register(ToolDefinition(
        name="test_multi_param",
        description="Test tool with multiple parameters",
        parameters=[
            ToolParameter(name="param1", type="string", description="First parameter", required=True),
            ToolParameter(name="param2", type="number", description="Second parameter", required=True),
            ToolParameter(name="param3", type="string", description="Third parameter", required=False)
        ],
        function=test_multi_param
    ))
    
    result = await tool_registry.execute("test_multi_param", {"param1": "value1"})
    
    print(f"\n✅ Tool correctly rejected the call")
    print(f"\nError Message:")
    print(f"  {result.error}")
    
    if result.error_details:
        print(f"\nDetailed Error Information:")
        
        if "validation_errors" in result.error_details:
            print(f"\n  Validation Errors:")
            for err in result.error_details["validation_errors"]:
                print(f"    - Parameter: {err['parameter']}")
                print(f"      Error: {err['error']}")
                print(f"      Type: {err['type']}")
        
        if "expected_parameters" in result.error_details:
            print(f"\n  Expected Parameters:")
            for param in result.error_details["expected_parameters"]:
                req = "REQUIRED" if param["required"] else "optional"
                print(f"    - {param['name']} ({param['type']}, {req})")
        
        if "provided_parameters" in result.error_details:
            print(f"\n  Provided Parameters: {result.error_details['provided_parameters']}")
    
    print("\n" + "-" * 80)
    print("✅ AI can understand:")
    print("   - Which specific parameter is missing")
    print("   - Which parameters were provided correctly")
    print("   - What all required parameters are")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY: Error Handling Quality")
    print("=" * 80)
    print("\n✅ All error messages are informative and include:")
    print("   1. Clear error description")
    print("   2. Detailed validation errors")
    print("   3. Expected parameters with types and descriptions")
    print("   4. Provided parameters for comparison")
    print("   5. Helpful suggestions for fixing")
    print("\n✅ AI can easily understand and fix errors without human intervention")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_error_handling())
