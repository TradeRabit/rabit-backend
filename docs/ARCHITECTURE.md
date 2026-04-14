# Architecture Overview

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Rabit Backend                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │   WebSocket  │      │   WebSocket  │                     │
│  │    Server    │◄────►│    Client    │                     │
│  │  (Clients)   │      │   (Drift)    │                     │
│  └──────┬───────┘      └──────┬───────┘                     │
│         │                     │                              │
│         │                     │                              │
│  ┌──────▼──────────────────────▼───────┐                    │
│  │         Agent Layer                  │                    │
│  │  ┌────────────────────────────────┐ │                    │
│  │  │      BaseAgent                 │ │                    │
│  │  │  - Memory Management           │ │                    │
│  │  │  - Auto Compression            │ │                    │
│  │  │  - Tool Calling                │ │                    │
│  │  └────────────────────────────────┘ │                    │
│  │                                      │                    │
│  │  ┌────────────────────────────────┐ │                    │
│  │  │    TradingAgent                │ │                    │
│  │  │    CustomAgent1                │ │                    │
│  │  │    CustomAgent2                │ │                    │
│  │  └────────────────────────────────┘ │                    │
│  └──────────────────────────────────────┘                    │
│         │                     │                              │
│         │                     │                              │
│  ┌──────▼─────────┐    ┌─────▼──────────┐                  │
│  │  Memory Layer  │    │   Tool Layer   │                  │
│  │                │    │                │                  │
│  │  ┌──────────┐  │    │  ┌──────────┐ │                  │
│  │  │  Global  │  │    │  │ Registry │ │                  │
│  │  │  Memory  │  │    │  │          │ │                  │
│  │  └──────────┘  │    │  └──────────┘ │                  │
│  │                │    │                │                  │
│  │  ┌──────────┐  │    │  ┌──────────┐ │                  │
│  │  │  Scoped  │  │    │  │  Tools   │ │                  │
│  │  │  Memory  │  │    │  │  - get_  │ │                  │
│  │  │  user_1  │  │    │  │  - calc_ │ │                  │
│  │  │  user_2  │  │    │  │  - ...   │ │                  │
│  │  └──────────┘  │    │  └──────────┘ │                  │
│  └────────────────┘    └────────────────┘                  │
│         │                     │                              │
│         │                     │                              │
│  ┌──────▼─────────────────────▼───────┐                    │
│  │      Compression Layer              │                    │
│  │  - Token Counting                   │                    │
│  │  - Smart Compression                │                    │
│  │  - Summarization                    │                    │
│  └─────────────────────────────────────┘                    │
│         │                                                    │
│         │                                                    │
│  ┌──────▼─────────────────────────────┐                    │
│  │      Claude API (Anthropic)        │                    │
│  │  - Message Processing               │                    │
│  │  - Tool Calling                     │                    │
│  │  - Response Generation              │                    │
│  └─────────────────────────────────────┘                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow

### 1. User Query Flow

```
User Input
    │
    ▼
WebSocket Server
    │
    ▼
Agent (BaseAgent/TradingAgent)
    │
    ├──► Memory Layer (Get History)
    │        │
    │        ▼
    │    Compression Layer (Check & Compress)
    │        │
    │        ▼
    ├──► Claude API (Process)
    │        │
    │        ▼
    │    Tool Calling? ──Yes──► Tool Registry
    │        │                       │
    │        No                      ▼
    │        │                  Execute Tool
    │        │                       │
    │        │                       ▼
    │        │                  Return Result
    │        │                       │
    │        ◄───────────────────────┘
    │        │
    │        ▼
    ├──► Memory Layer (Save Response)
    │
    ▼
Response to User
```

### 2. Tool Execution Flow

```
Agent Calls Tool
    │
    ▼
Tool Registry
    │
    ├──► Validate Tool Exists?
    │        │
    │        No ──► Return Error (Tool Not Found)
    │        │
    │        Yes
    │        │
    │        ▼
    ├──► Validate Parameters?
    │        │
    │        No ──► Return Error (Invalid Parameters)
    │        │           │
    │        │           ├─ Missing required params
    │        │           ├─ Wrong types
    │        │           └─ Unexpected params
    │        │
    │        Yes
    │        │
    │        ▼
    ├──► Execute Tool Function
    │        │
    │        ├──► Success ──► Return Data
    │        │
    │        └──► Error ──► Return Error Details
    │                          │
    │                          ├─ Error type
    │                          ├─ Error message
    │                          └─ Suggestions
    │
    ▼
Return ToolResult to Agent
```

### 3. Memory Management Flow

```
Message Added
    │
    ▼
Scope ID Provided?
    │
    ├──► Yes ──► Add to Scoped Memory
    │                │
    │                └─ memory[scope_id].append(message)
    │
    └──► No ──► Add to Global Memory
                     │
                     └─ global_memory.append(message)

Get Messages
    │
    ▼
Scope ID Provided?
    │
    ├──► Yes ──► Get from Scoped Memory
    │                │
    │                └─ return memory[scope_id]
    │
    └──► No ──► Get from Global Memory
                     │
                     └─ return global_memory
```

### 4. Compression Flow

```
Process Message
    │
    ▼
Get Conversation History
    │
    ▼
Count Tokens
    │
    ▼
Tokens > Max?
    │
    ├──► No ──► Continue Normal Processing
    │
    └──► Yes ──► Trigger Compression
                     │
                     ▼
                 Keep System Message
                     │
                     ▼
                 Keep Last 2 Messages
                     │
                     ▼
                 Summarize Middle Messages
                     │
                     ├──► Success ──► Use Summary
                     │
                     └──► Fail ──► Truncate Instead
                     │
                     ▼
                 Return Compressed History
```

## 📦 Component Details

### Agent Layer

**Responsibilities:**
- Process user queries
- Manage conversation flow
- Coordinate memory, compression, and tools
- Handle Claude API communication

**Key Classes:**
- `BaseAgent`: Core agent functionality
- `TradingAgent`: Trading-specific agent
- Custom agents (extensible)

### Memory Layer

**Responsibilities:**
- Store conversation history
- Manage scoped and global memory
- Provide message retrieval
- Handle memory cleanup

**Key Classes:**
- `ConversationMemory`: Memory management
- `Message`: Message model

### Compression Layer

**Responsibilities:**
- Monitor token usage
- Compress conversations when needed
- Summarize message history
- Maintain conversation context

**Key Classes:**
- `ConversationCompressor`: Compression logic

### Tool Layer

**Responsibilities:**
- Register and manage tools
- Validate tool parameters
- Execute tool functions
- Provide detailed error messages

**Key Classes:**
- `ToolRegistry`: Tool management
- `ToolDefinition`: Tool schema
- `ToolParameter`: Parameter definition
- `ToolResult`: Execution result

## 🔌 Integration Points

### 1. Claude API Integration

```python
# Agent → Claude API
response = client.messages.create(
    model=model,
    max_tokens=1024,
    system=system_prompt,
    messages=messages,
    tools=tools_schema  # Optional
)
```

### 2. Tool Integration

```python
# Register Tool
tool_registry.register(ToolDefinition(
    name="tool_name",
    description="Tool description",
    parameters=[...],
    function=tool_function
))

# Execute Tool
result = await tool_registry.execute(
    "tool_name",
    {"param": "value"}
)
```

### 3. Memory Integration

```python
# Add Message
memory.add_message(
    Message(role="user", content="Hello"),
    scope_id="user_123"
)

# Get Messages
messages = memory.get_messages(
    scope_id="user_123",
    limit=10
)
```

### 4. WebSocket Integration (TODO)

```python
# Drift WebSocket Client
client = DriftWSClient()
await client.connect()
await client.subscribe("market_data", callback)

# WebSocket Server
# TODO: Implement server for client connections
```

## 🎯 Design Patterns

### 1. Registry Pattern
- **Used in**: Tool management
- **Purpose**: Central registration and lookup
- **Benefits**: Extensible, maintainable

### 2. Strategy Pattern
- **Used in**: Agent implementations
- **Purpose**: Different agent behaviors
- **Benefits**: Flexible, reusable

### 3. Factory Pattern
- **Used in**: Message creation
- **Purpose**: Consistent object creation
- **Benefits**: Standardized, type-safe

### 4. Singleton Pattern
- **Used in**: Tool registry, settings
- **Purpose**: Single instance management
- **Benefits**: Global access, consistency

## 🔒 Security Considerations

### 1. API Key Management
- Store in environment variables
- Never commit to repository
- Use secrets management in production

### 2. Input Validation
- Validate all tool parameters
- Type checking
- Sanitize user input

### 3. Error Handling
- Don't expose internal errors
- Log errors securely
- Provide helpful but safe messages

### 4. Rate Limiting (TODO)
- Limit API calls per user
- Prevent abuse
- Monitor usage

## 📈 Scalability Considerations

### 1. Memory Management
- **Current**: In-memory storage
- **Future**: Redis for distributed memory
- **Benefits**: Horizontal scaling

### 2. Tool Execution
- **Current**: Synchronous execution
- **Future**: Async task queue (Celery)
- **Benefits**: Better performance

### 3. WebSocket Connections
- **Current**: Single server
- **Future**: Load balancer + multiple servers
- **Benefits**: Handle more connections

### 4. Database
- **Current**: None
- **Future**: PostgreSQL/MongoDB
- **Benefits**: Persistent storage

## 🔧 Configuration

### Environment-based Configuration

```
Development:
- DEBUG=true
- Detailed logging
- Local services

Production:
- DEBUG=false
- Error logging only
- Cloud services
- Monitoring enabled
```

### Feature Flags (TODO)

```python
FEATURES = {
    "auto_compression": True,
    "tool_calling": True,
    "memory_persistence": False,  # TODO
    "rate_limiting": False,  # TODO
}
```

## 📊 Monitoring Points

### 1. Metrics to Track
- API call latency
- Token usage
- Tool execution time
- Memory usage
- Error rates

### 2. Logging Points
- User queries
- Tool executions
- Errors and exceptions
- Performance metrics

### 3. Alerts (TODO)
- High error rate
- API quota exceeded
- Memory threshold
- Performance degradation

---

**Last Updated**: 2026-04-14
**Version**: 1.0.0
