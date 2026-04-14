"""Test setup and basic functionality"""
import asyncio
from utils.logger import get_logger
from agents import ConversationMemory, Message, ConversationCompressor, tool_registry, register_example_tools

logger = get_logger(__name__)


def test_memory():
    """Test memory management"""
    logger.info("\n=== Testing Memory Management ===")
    
    memory = ConversationMemory()
    
    # Test global memory
    msg1 = Message(role="user", content="Hello global")
    memory.add_message(msg1)
    
    # Test scoped memory
    msg2 = Message(role="user", content="Hello user 1")
    memory.add_message(msg2, scope_id="user_1")
    
    msg3 = Message(role="user", content="Hello user 2")
    memory.add_message(msg3, scope_id="user_2")
    
    # Verify
    global_msgs = memory.get_messages()
    user1_msgs = memory.get_messages(scope_id="user_1")
    user2_msgs = memory.get_messages(scope_id="user_2")
    
    logger.info(f"Global messages: {len(global_msgs)}")
    logger.info(f"User 1 messages: {len(user1_msgs)}")
    logger.info(f"User 2 messages: {len(user2_msgs)}")
    logger.info(f"All scopes: {memory.get_all_scopes()}")
    
    assert len(global_msgs) == 1
    assert len(user1_msgs) == 1
    assert len(user2_msgs) == 1
    
    logger.info("✅ Memory test passed")


def test_compression():
    """Test conversation compression"""
    logger.info("\n=== Testing Compression ===")
    
    compressor = ConversationCompressor(max_tokens=100)
    
    # Create long conversation
    messages = [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
        {"role": "user", "content": "Can you help me with trading?"},
        {"role": "assistant", "content": "Of course! I can help with trading."},
        {"role": "user", "content": "What's the price of SOL?"},
    ]
    
    token_count = compressor.count_tokens(messages)
    needs_compression = compressor.needs_compression(messages)
    
    logger.info(f"Token count: {token_count}")
    logger.info(f"Needs compression: {needs_compression}")
    
    logger.info("✅ Compression test passed")


def test_tools():
    """Test tool registry"""
    logger.info("\n=== Testing Tool Registry ===")
    
    # Register example tools
    register_example_tools()
    
    # List tools
    tools = tool_registry.list_tools()
    logger.info(f"Registered tools: {len(tools)}")
    
    for tool in tools:
        logger.info(f"  - {tool.name}: {tool.description}")
    
    # Get schema
    schema = tool_registry.get_tools_schema()
    logger.info(f"Tool schemas: {len(schema)}")
    
    assert len(tools) == 3
    assert len(schema) == 3
    
    logger.info("✅ Tool registry test passed")


async def test_tool_execution():
    """Test tool execution with error handling"""
    logger.info("\n=== Testing Tool Execution ===")
    
    register_example_tools()
    
    # Test successful execution
    result = await tool_registry.execute(
        "get_market_price",
        {"symbol": "SOL", "market": "drift"}
    )
    logger.info(f"Success: {result.success}")
    logger.info(f"Data: {result.data}")
    
    assert result.success == True
    
    # Test missing parameter
    result = await tool_registry.execute(
        "get_market_price",
        {"market": "drift"}  # Missing 'symbol'
    )
    logger.info(f"Success: {result.success}")
    logger.info(f"Error: {result.error}")
    logger.info(f"Error details: {result.error_details}")
    
    assert result.success == False
    assert "validation_errors" in result.error_details
    
    # Test wrong tool name
    result = await tool_registry.execute(
        "non_existent_tool",
        {}
    )
    logger.info(f"Success: {result.success}")
    logger.info(f"Error: {result.error}")
    
    assert result.success == False
    
    logger.info("✅ Tool execution test passed")


async def main():
    """Run all tests"""
    logger.info("Starting setup tests...\n")
    
    try:
        test_memory()
        test_compression()
        test_tools()
        await test_tool_execution()
        
        logger.info("\n" + "="*50)
        logger.info("✅ All tests passed!")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
