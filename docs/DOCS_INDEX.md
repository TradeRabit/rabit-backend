# 📑 Complete Documentation Index

Selamat datang di dokumentasi Rabit Backend! Ini adalah index lengkap untuk semua dokumentasi.

> **💡 Tip**: Untuk navigasi yang lebih mudah, lihat [Main Documentation](README.md)

---

## 📚 Documentation Structure

### 🚀 [Getting Started](getting-started/)

1. **[Quick Start Guide](getting-started/QUICKSTART.md)** - 5-minute setup
   - Step-by-step setup guide
   - Example code snippets
   - Common use cases
   - Troubleshooting tips

2. **[Features Overview](getting-started/FEATURES.md)** - Feature documentation
   - Auto conversation compression
   - Memory management (scoped & global)
   - Tool calling system
   - Detailed error handling
   - Usage examples

### 🏗️ [Architecture](architecture/)

3. **[System Architecture](architecture/ARCHITECTURE.md)** - System architecture
   - Architecture diagrams
   - Data flow diagrams
   - Component details
   - Integration points
   - Design patterns
   - Scalability considerations

4. **[Project Summary](architecture/PROJECT_SUMMARY.md)** - Project overview
   - Project statistics
   - Key components
   - Configuration
   - Usage examples
   - Next steps

5. **[Restructure Summary](architecture/RESTRUCTURE_SUMMARY.md)** - Recent changes
   - Architectural changes
   - Migration guide
   - Breaking changes

### 📡 [API Reference](api/)

6. **[API Reference](api/API_REFERENCE.md)** - Complete API reference
   - Agent classes
   - Memory classes
   - Compression classes
   - Tool classes
   - Example tools
   - Error handling

7. **[API Documentation](api/API_DOCUMENTATION.md)** - Additional API details
   - Endpoint documentation
   - Request/response formats
   - Authentication

### 🤖 [Agents](agents/)

8. **[Agent Structure](agents/AGENTS_STRUCTURE.md)** - Agent module organization
   - Module structure
   - Agent types
   - Creating custom agents

9. **[Agent Visual Guide](agents/AGENTS_VISUAL.md)** - Visual representation
   - Architecture diagrams
   - Flow charts
   - Component relationships

10. **[Assistant Types](agents/ASSISTANT_TYPES.md)** - Different assistant types
    - Trading assistant
    - Research assistant
    - Custom assistants

11. **[Context Implementation](agents/CONTEXT_IMPLEMENTATION.md)** - Trading context management
    - Exchange selection (drift/backpack)
    - Trading modes (global/asset-locked)
    - Context API
    - Integration guide

### 📊 [WebSocket & Real-time Data](websocket/)

11. **[WebSocket Structure](websocket/WS_STRUCTURE.md)** - WebSocket module overview
    - Module organization
    - Data sources (Drift, Backpack, Binance, CoinGecko)
    - Models and handlers
    - Usage examples

12. **[Data Sources](websocket/DATA_SOURCES.md)** - All available data sources
    - Exchange integrations
    - API integrations
    - Data formats

13. **[Trading Assets](websocket/TRADING_ASSETS.md)** - Supported trading assets
    - Available symbols
    - Asset categories
    - Market coverage

#### Backpack Exchange
14. **[Backpack Integration](websocket/BACKPACK_INTEGRATION.md)** - Complete guide
    - WebSocket protocol
    - Data mapping
    - Use cases
    - Best practices

15. **[Backpack Quick Start](websocket/BACKPACK_QUICKSTART.md)** - 5-minute setup
    - Quick examples
    - Common use cases
    - Troubleshooting

16. **[Backpack Implementation](websocket/BACKPACK_IMPLEMENTATION_SUMMARY.md)** - Implementation details
    - Technical details
    - Architecture decisions
    - Testing

17. **[WebSocket Implementation](websocket/WS_IMPLEMENTATION_SUMMARY.md)** - Overall WS implementation
    - Implementation summary
    - Architecture overview

### � [Integrations](integrations/)

#### Data & APIs
18. **[CoinGecko Integration](integrations/COINGECKO_INTEGRATION.md)** - Coin information API
    - API integration
    - Database caching
    - Rate limiting

19. **[News Monitoring](integrations/NEWS_MONITORING.md)** - Real-time news tracking
    - News sources
    - AI sentiment analysis
    - WebSocket broadcasting

20. **[News Sources](integrations/NEWS_SOURCES.md)** - Available news sources
    - Source list
    - Configuration
    - API details

21. **[Web Search](integrations/WEB_SEARCH.md)** - Web search capabilities
    - Search integration
    - Usage examples

#### AI & Memory
22. **[OpenRouter Integration](integrations/OPENROUTER_INTEGRATION.md)** - AI model routing
    - Model selection
    - Configuration
    - Usage examples

23. **[OpenRouter Caching](integrations/OPENROUTER_CACHING.md)** - Prompt caching
    - Cache configuration
    - Performance optimization

24. **[OpenRouter Models](integrations/OPENROUTER_MODELS.md)** - Available models
    - Model list
    - Capabilities
    - Pricing

25. **[Mem0 Integration](integrations/MEM0_INTEGRATION.md)** - User memory management
    - Memory types
    - Configuration
    - Usage examples

26. **[Session Persistence](integrations/SESSION_PERSISTENCE.md)** - Session management
    - Session storage
    - State management

### 🛠️ [Tools](tools/)

27. **[Get Price Tool](tools/GET_PRICE_TOOL.md)** - Real-time price fetching
    - Usage examples
    - Supported exchanges
    - Data format

28. **[Tools Summary](tools/TOOLS_SUMMARY.md)** - All available tools
    - Tool list
    - Capabilities
    - Usage guide

### 💻 [Development](development/)

29. **[Development Guide](development/DEVELOPMENT.md)** - Complete development workflow
    - Development setup
    - Coding standards
    - Common tasks
    - Testing guide
    - Debugging tips
    - Best practices

30. **[Implementation Checklist](development/IMPLEMENTATION_CHECKLIST.md)** - Feature tracking
    - Completed features
    - Pending features
    - Sprint goals
    - Progress metrics
    - Known issues

31. **[Mobile Data Requirements](development/MOBILE_DATA_REQUIREMENTS.md)** - Mobile app specs
    - Data requirements
    - API endpoints
    - Mobile optimization

32. **[Implementation Summary](development/IMPLEMENTATION_SUMMARY.md)** - Recent implementations
    - Feature summaries
    - Technical details
    - Integration notes

33. **[Documentation Reorganization](development/DOCUMENTATION_REORGANIZATION.md)** - Docs structure
    - Documentation changes
    - File organization
    - Migration notes

## 🎯 Quick Navigation

### For New Users
1. Start with [Main Documentation](README.md)
2. Follow [Quick Start Guide](getting-started/QUICKSTART.md)
3. Read [Features Overview](getting-started/FEATURES.md)
4. Check [API Reference](api/API_REFERENCE.md) when needed

### For Developers
1. Read [Development Guide](development/DEVELOPMENT.md)
2. Study [System Architecture](architecture/ARCHITECTURE.md)
3. Check [Implementation Checklist](development/IMPLEMENTATION_CHECKLIST.md)
4. Refer to [API Reference](api/API_REFERENCE.md)

### For Contributors
1. Read [Development Guide](development/DEVELOPMENT.md)
2. Check [Implementation Checklist](development/IMPLEMENTATION_CHECKLIST.md)
3. Follow coding standards in [Development Guide](development/DEVELOPMENT.md)
4. Update relevant documentation

### For Project Managers
1. Read [Project Summary](architecture/PROJECT_SUMMARY.md)
2. Check [Implementation Checklist](development/IMPLEMENTATION_CHECKLIST.md)
3. Review [System Architecture](architecture/ARCHITECTURE.md)

## 📋 Documentation by Topic

### Agent System
- [Features Overview](getting-started/FEATURES.md) - Agent features overview
- [API Reference](api/API_REFERENCE.md) - BaseAgent API
- [System Architecture](architecture/ARCHITECTURE.md) - Agent architecture
- [Development Guide](development/DEVELOPMENT.md) - Creating custom agents
- [Agent Structure](agents/AGENTS_STRUCTURE.md) - Agent module organization
- [Get Price Tool](tools/GET_PRICE_TOOL.md) - Real-time price tool documentation

### WebSocket & Real-time Data
- [WebSocket Structure](websocket/WS_STRUCTURE.md) - WebSocket module overview
- [Backpack Integration](websocket/BACKPACK_INTEGRATION.md) - Backpack Exchange integration
- [Backpack Quick Start](websocket/BACKPACK_QUICKSTART.md) - Backpack quick start
- [CoinGecko Integration](integrations/COINGECKO_INTEGRATION.md) - CoinGecko API integration
- [News Monitoring](integrations/NEWS_MONITORING.md) - News monitoring system
- [Data Sources](websocket/DATA_SOURCES.md) - All data sources overview

### Memory Management
- [Features Overview](getting-started/FEATURES.md) - Memory features
- [API Reference](api/API_REFERENCE.md) - Memory API
- [System Architecture](architecture/ARCHITECTURE.md) - Memory architecture
- [Development Guide](development/DEVELOPMENT.md) - Using memory
- [Mem0 Integration](integrations/MEM0_INTEGRATION.md) - Mem0 integration

### Tool System
- [Features Overview](getting-started/FEATURES.md) - Tool system overview
- [API Reference](api/API_REFERENCE.md) - Tool API
- [System Architecture](architecture/ARCHITECTURE.md) - Tool architecture
- [Development Guide](development/DEVELOPMENT.md) - Creating tools
- [Tools Summary](tools/TOOLS_SUMMARY.md) - All tools

### Compression
- [Features Overview](getting-started/FEATURES.md) - Compression features
- [API Reference](api/API_REFERENCE.md) - Compression API
- [System Architecture](architecture/ARCHITECTURE.md) - Compression flow

### Configuration
- [Main README](../README.md) - Basic configuration
- [Quick Start Guide](getting-started/QUICKSTART.md) - Environment setup
- [Development Guide](development/DEVELOPMENT.md) - Adding configuration

### Testing
- [Quick Start Guide](getting-started/QUICKSTART.md) - Running tests
- [Development Guide](development/DEVELOPMENT.md) - Writing tests
- [Implementation Checklist](development/IMPLEMENTATION_CHECKLIST.md) - Test coverage

### Deployment
- [Main README](../README.md) - Docker setup
- [System Architecture](architecture/ARCHITECTURE.md) - Scalability
- [Implementation Checklist](development/IMPLEMENTATION_CHECKLIST.md) - Deployment status

## 🔍 Search by Keyword

### Setup & Installation
- [Main README](../README.md) - Main setup
- [Quick Start Guide](getting-started/QUICKSTART.md) - Quick setup
- [Development Guide](development/DEVELOPMENT.md) - Dev setup

### Usage Examples
- [Main README](../README.md) - Basic examples
- [Quick Start Guide](getting-started/QUICKSTART.md) - Quick examples
- [Features Overview](getting-started/FEATURES.md) - Feature examples
- [API Reference](api/API_REFERENCE.md) - API examples

### API Documentation
- [API Reference](api/API_REFERENCE.md) - Complete API reference
- [API Documentation](api/API_DOCUMENTATION.md) - Additional details

### Architecture & Design
- [System Architecture](architecture/ARCHITECTURE.md) - System architecture
- [Project Summary](architecture/PROJECT_SUMMARY.md) - Project structure

### Development Guide
- [Development Guide](development/DEVELOPMENT.md) - Complete dev guide

### Progress & Status
- [Implementation Checklist](development/IMPLEMENTATION_CHECKLIST.md) - Implementation status
- [Project Summary](architecture/PROJECT_SUMMARY.md) - Project overview

## 📊 Documentation Statistics

- **Total Documents**: 33+
- **Categories**: 8 (Getting Started, Architecture, API, Agents, WebSocket, Integrations, Tools, Development)
- **Total Pages**: ~200+ pages
- **Code Examples**: 100+
- **Diagrams**: 10+
- **Last Updated**: 2026-04-16

## 🔄 Documentation Updates

### Recent Updates (2026-04-16)
- ✅ **Added Trading Context Management** - Exchange & asset tracking
- ✅ **Reorganized documentation structure** - Moved files to subfolders
- ✅ Added main [Documentation README](README.md)
- ✅ Added README for Drift, Binance, Backpack modules
- ✅ Added Backpack Exchange integration
- ✅ Added Backpack quick start guide
- ✅ Updated WebSocket structure documentation
- ✅ Added comprehensive data source documentation
- ✅ Updated requirements.txt with bpx-py

### Previous Updates (2026-04-14)
- ✅ Created complete documentation set
- ✅ Added architecture diagrams
- ✅ Added API reference
- ✅ Added development guide
- ✅ Added quick start guide

### Planned Updates
- [ ] Add video tutorials
- [ ] Add more code examples
- [ ] Add FAQ section
- [ ] Add troubleshooting guide
- [ ] Add deployment guide

## 💡 Documentation Tips

### For Reading
1. Start with overview documents (README, QUICKSTART)
2. Deep dive into specific topics as needed
3. Use API reference for detailed information
4. Check examples for practical usage

### For Contributing
1. Keep documentation up-to-date with code
2. Add examples for new features
3. Update API reference for new APIs
4. Follow documentation style guide

### For Maintaining
1. Review documentation regularly
2. Update outdated information
3. Add missing documentation
4. Improve clarity and examples

## 🤝 Contributing to Documentation

### How to Contribute
1. Identify documentation gaps
2. Create/update documentation
3. Add examples and diagrams
4. Submit pull request

### Documentation Standards
- Clear and concise writing
- Code examples for all features
- Diagrams for complex concepts
- Keep documentation in sync with code

## 📞 Getting Help

### Documentation Issues
- Found outdated information? Open an issue
- Need clarification? Ask in discussions
- Want to contribute? Submit a PR

### Code Issues
- Check [DEVELOPMENT.md](DEVELOPMENT.md) for debugging
- Check [QUICKSTART.md](QUICKSTART.md) for setup issues
- Check [API_REFERENCE.md](API_REFERENCE.md) for API usage

## 🎓 Learning Path

### Beginner Path
1. [README.md](README.md) - Understand the project
2. [QUICKSTART.md](QUICKSTART.md) - Get it running
3. [FEATURES.md](FEATURES.md) - Learn features
4. [API_REFERENCE.md](API_REFERENCE.md) - Use the API

### Intermediate Path
1. [ARCHITECTURE.md](ARCHITECTURE.md) - Understand design
2. [DEVELOPMENT.md](DEVELOPMENT.md) - Start developing
3. [API_REFERENCE.md](API_REFERENCE.md) - Deep dive into API
4. [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) - See what's next

### Advanced Path
1. [ARCHITECTURE.md](ARCHITECTURE.md) - Master the architecture
2. [DEVELOPMENT.md](DEVELOPMENT.md) - Advanced development
3. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Full project understanding
4. Contribute to the project!

---

**Last Updated**: 2026-04-16  
**Version**: 2.0.0  
**Maintained by**: Rabit Backend Team

## 📝 Quick Links

### Essential Docs
- [Main Documentation](README.md) - Start here!
- [Quick Start Guide](getting-started/QUICKSTART.md)
- [Features Overview](getting-started/FEATURES.md)
- [API Reference](api/API_REFERENCE.md)
- [System Architecture](architecture/ARCHITECTURE.md)
- [Development Guide](development/DEVELOPMENT.md)

### WebSocket & Data
- [WebSocket Structure](websocket/WS_STRUCTURE.md)
- [Backpack Integration](websocket/BACKPACK_INTEGRATION.md)
- [Backpack Quick Start](websocket/BACKPACK_QUICKSTART.md)
- [Data Sources](websocket/DATA_SOURCES.md)

### Integrations
- [CoinGecko](integrations/COINGECKO_INTEGRATION.md)
- [OpenRouter](integrations/OPENROUTER_INTEGRATION.md)
- [Mem0](integrations/MEM0_INTEGRATION.md)
- [News Monitoring](integrations/NEWS_MONITORING.md)

### Development
- [Implementation Checklist](development/IMPLEMENTATION_CHECKLIST.md)
- [Project Summary](architecture/PROJECT_SUMMARY.md)
