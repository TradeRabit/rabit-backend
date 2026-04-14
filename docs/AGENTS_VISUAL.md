# Agents Module - Visual Guide

## 📦 Module Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    agents/ (Main Module)                     │
│                                                               │
│  Centralized exports for all agent features                 │
│  ✓ BaseAgent, TradingAgent                                  │
│  ✓ ConversationMemory, Message                              │
│  ✓ ConversationCompressor                                   │
│  ✓ ToolRegistry, ToolDefinition, ToolParameter, ToolResult │
│  ✓ tool_registry (global instance)                          │
│  ✓ register_example_tools                                   │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    ┌────────┐    ┌────────┐    ┌──────────┐    ┌────────┐
    │  core  │    │ memory │    │compression│   │ tools  │
    └────────┘    └────────┘    └──────────┘    └────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    ┌────────┐    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │BaseAgent│   │Conversation│ │Compressor│  │ToolRegistry
    │Trading  │   │Memory      │ │          │  │ToolDef
    │Agent    │   │Message     │ │          │  │ToolParam
    └────────┘    └──────────┘  └──────────┘  └──────────┘
         │
         ▼
    ┌────────┐
    │examples│
    └────────┘
         │
         ▼
    ┌──────────────┐
    │trading_tools │
    │register_tools│
    └──────────────┘
```

## 🎯 Feature Organization

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Features                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. CORE AGENTS (agents/core/)                        │   │
│  │    ├─ BaseAgent                                      │   │
│  │    │  ├─ Message management                          │   │
│  │    │  ├─ Tool calling                                │   │
│  │    │  └─ Auto-compression                            │   │
│  │    └─ TradingAgent (example)                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. MEMORY (agents/memory/)                           │   │
│  │    ├─ Global Memory                                  │   │
│  │    ├─ Scoped Memory (per user/session)              │   │
│  │    ├─ Message History                                │   │
│  │    └─ Memory Operations                              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. COMPRESSION (agents/compression/)                 │   │
│  │    ├─ Token Counting                                 │   │
│  │    ├─ Compression Detection                          │   │
│  │    ├─ Smart Summarization                            │   │
│  │    └─ Fallback Truncation                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. TOOLS (agents/tools/)                             │   │
│  │    ├─ Tool Registry                                  │   │
│  │    ├─ Tool Definitions                               │   │
│  │    ├─ Parameter Validation                           │   │
│  │    ├─ Tool Execution                                 │   │
│  │    └─ Error Handling                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 5. EXAMPLES (agents/examples/)                       │   │
│  │    ├─ Trading Tools                                  │   │
│  │    │  ├─ get_market_price                            │   │
│  │    │  ├─ calculate_position_size                     │   │
│  │    │  └─ get_account_info                            │   │
│  │    └─ Tool Registration Helper                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 📂 File Structure

```
agents/
│
├── __init__.py
│   └─ Centralized exports
│
├── core/
│   ├── __init__.py
│   ├── base.py
│   │   └─ BaseAgent class
│   │      ├─ __init__()
│   │      ├─ add_message()
│   │      ├─ get_conversation_history()
│   │      ├─ clear_history()
│   │      ├─ process()
│   │      ├─ _process_with_tools()
│   │      └─ _format_tool_error()
│   │
│   └── trading_agent.py
│       └─ TradingAgent class
│          ├─ __init__()
│          └─ process_trading_query()
│
├── memory/
│   ├── __init__.py
│   └── conversation.py
│       ├─ Message class
│       │  ├─ role
│       │  ├─ content
│       │  └─ timestamp
│       │
│       └─ ConversationMemory class
│          ├─ add_message()
│          ├─ get_messages()
│          ├─ clear_scope()
│          ├─ clear_global()
│          ├─ get_all_scopes()
│          ├─ get_scope_size()
│          └─ get_global_size()
│
├── compression/
│   ├── __init__.py
│   └── compressor.py
│       └─ ConversationCompressor class
│          ├─ count_tokens()
│          ├─ needs_compression()
│          ├─ compress()
│          ├─ _create_summary_prompt()
│          └─ _truncate_messages()
│
├── tools/
│   ├── __init__.py
│   ├── definitions.py
│   │   ├─ ToolParameter class
│   │   ├─ ToolDefinition class
│   │   └─ ToolResult class
│   │
│   └── registry.py
│       ├─ ToolRegistry class
│       │  ├─ register()
│       │  ├─ get_tool()
│       │  ├─ list_tools()
│       │  ├─ get_tools_schema()
│       │  ├─ execute()
│       │  └─ _validate_parameters()
│       │
│       └─ tool_registry (global instance)
│
└── examples/
    ├── __init__.py
    └── trading_tools.py
        ├─ get_market_price()
        ├─ calculate_position_size()
        ├─ get_account_info()
        └─ register_example_tools()
```

## 🔄 Data Flow

```
User Input
    │
    ▼
┌─────────────────────────────────────┐
│  agents.core.BaseAgent              │
│  ├─ add_message()                   │
│  ├─ get_conversation_history()      │
│  └─ process()                       │
└─────────────────────────────────────┘
    │
    ├──────────────────────────────────┐
    │                                  │
    ▼                                  ▼
┌──────────────────────┐    ┌──────────────────────┐
│ agents.memory        │    │ agents.compression   │
│ ConversationMemory   │    │ ConversationCompressor
│ ├─ add_message()     │    │ ├─ count_tokens()    │
│ └─ get_messages()    │    │ ├─ needs_compression │
└──────────────────────┘    │ └─ compress()        │
    │                       └──────────────────────┘
    │                                  │
    └──────────────────────┬───────────┘
                           │
                           ▼
                    ┌──────────────────┐
                    │ Claude API       │
                    │ (Anthropic)      │
                    └──────────────────┘
                           │
                    ┌──────▼──────────┐
                    │ Tool Calling?   │
                    └──────┬──────────┘
                           │
                    ┌──────▼──────────┐
                    │ Yes / No        │
                    └──────┬──────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
        ┌────────────┐            ┌──────────────┐
        │ No Tools   │            │ Use Tools    │
        │ Return     │            │              │
        │ Response   │            ▼              │
        └────────────┘    ┌──────────────────┐  │
            │             │ agents.tools     │  │
            │             │ ToolRegistry     │  │
            │             │ ├─ execute()     │  │
            │             │ ├─ validate()    │  │
            │             │ └─ error_handle()│  │
            │             └──────────────────┘  │
            │                     │             │
            │                     ▼             │
            │             ┌──────────────────┐  │
            │             │ Tool Result      │  │
            │             │ ├─ success       │  │
            │             │ ├─ data          │  │
            │             │ ├─ error         │  │
            │             │ └─ error_details │  │
            │             └──────────────────┘  │
            │                     │             │
            └─────────────┬───────┘             │
                          │                     │
                          ▼                     │
                    ┌──────────────┐            │
                    │ Final        │            │
                    │ Response     │            │
                    └──────────────┘            │
                          │                     │
                          └─────────────────────┘
                                  │
                                  ▼
                            Response to User
```

## 🎯 Import Paths

```
┌─────────────────────────────────────────────────────────────┐
│                    Import Paths                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Main Module (Recommended)                                  │
│  ─────────────────────────────────────────────────────────  │
│  from agents import (                                       │
│      BaseAgent,                                             │
│      TradingAgent,                                          │
│      ConversationMemory,                                    │
│      Message,                                               │
│      ConversationCompressor,                                │
│      ToolRegistry,                                          │
│      ToolDefinition,                                        │
│      ToolParameter,                                         │
│      ToolResult,                                            │
│      tool_registry,                                         │
│      register_example_tools                                 │
│  )                                                          │
│                                                               │
│  Submodules (If Needed)                                     │
│  ─────────────────────────────────────────────────────────  │
│  from agents.core import BaseAgent, TradingAgent            │
│  from agents.memory import ConversationMemory, Message      │
│  from agents.compression import ConversationCompressor      │
│  from agents.tools import (                                 │
│      ToolRegistry,                                          │
│      ToolDefinition,                                        │
│      ToolParameter,                                         │
│      ToolResult,                                            │
│      tool_registry                                          │
│  )                                                          │
│  from agents.examples import register_example_tools         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Usage Examples

```
┌─────────────────────────────────────────────────────────────┐
│                    Usage Examples                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Create Agent                                            │
│  ─────────────────────────────────────────────────────────  │
│  from agents import TradingAgent                            │
│                                                               │
│  agent = TradingAgent(scope_id="user_123")                  │
│  response = await agent.process_trading_query("...")        │
│                                                               │
│  2. Register Tool                                           │
│  ─────────────────────────────────────────────────────────  │
│  from agents import tool_registry, ToolDefinition           │
│                                                               │
│  tool_registry.register(ToolDefinition(...))                │
│                                                               │
│  3. Use Memory                                              │
│  ─────────────────────────────────────────────────────────  │
│  from agents import ConversationMemory, Message             │
│                                                               │
│  memory = ConversationMemory()                              │
│  memory.add_message(Message(...), scope_id="user_1")        │
│                                                               │
│  4. Register Example Tools                                  │
│  ─────────────────────────────────────────────────────────  │
│  from agents import register_example_tools                  │
│                                                               │
│  register_example_tools()                                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

**Last Updated**: 2026-04-14
**Version**: 1.0.0
