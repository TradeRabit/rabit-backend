# 📚 Rabit Backend Documentation

Welcome to the comprehensive documentation for Rabit Backend - an AI-powered trading assistant with real-time market data integration.

## 🚀 Quick Navigation

### 🎯 New to Rabit?
Start here → [Quick Start Guide](getting-started/QUICKSTART.md)

### 🔍 Looking for something specific?
Use the navigation below or check the [Documentation Index](DOCS_INDEX.md)

---

## 📖 Documentation Structure

### 1️⃣ [Getting Started](getting-started/)
Perfect for beginners and quick setup.

- **[Quick Start Guide](getting-started/QUICKSTART.md)** - Get up and running in 5 minutes
- **[Features Overview](getting-started/FEATURES.md)** - Explore what Rabit can do

**Start here if you're new!** 👈

---

### 2️⃣ [Architecture](architecture/)
Understand how Rabit is built.

- **[System Architecture](architecture/ARCHITECTURE.md)** - High-level system design
- **[Project Summary](architecture/PROJECT_SUMMARY.md)** - Project overview and statistics
- **[Restructure Summary](architecture/RESTRUCTURE_SUMMARY.md)** - Recent architectural changes

**For developers and architects** 🏗️

---

### 3️⃣ [API Reference](api/)
Complete API documentation.

- **[API Reference](api/API_REFERENCE.md)** - Complete API documentation
- **[API Documentation](api/API_DOCUMENTATION.md)** - Additional API details

**For integration and development** 📡

---

### 4️⃣ [Agents](agents/)
AI agent system documentation.

- **[Agent Structure](agents/AGENTS_STRUCTURE.md)** - Agent module organization
- **[Agent Visual Guide](agents/AGENTS_VISUAL.md)** - Visual representation of agents
- **[Assistant Types](agents/ASSISTANT_TYPES.md)** - Different types of AI assistants

**For AI agent development** 🤖

---

### 5️⃣ [WebSocket & Real-time Data](websocket/)
Real-time market data integration.

- **[WebSocket Structure](websocket/WS_STRUCTURE.md)** - WebSocket module overview
- **[Data Sources](websocket/DATA_SOURCES.md)** - All available data sources
- **[Trading Assets](websocket/TRADING_ASSETS.md)** - Supported trading assets

#### Exchange Integrations:
- **[Backpack Exchange](websocket/BACKPACK_INTEGRATION.md)** - Full integration guide
  - [Quick Start](websocket/BACKPACK_QUICKSTART.md) - Get started in 5 minutes
  - [Implementation Summary](websocket/BACKPACK_IMPLEMENTATION_SUMMARY.md)
- **[Drift Protocol](websocket/)** - Futures market data
- **[Binance](websocket/)** - OHLC/candlestick data

**For real-time trading data** 📊

---

### 6️⃣ [Integrations](integrations/)
Third-party service integrations.

#### Data & APIs:
- **[CoinGecko Integration](integrations/COINGECKO_INTEGRATION.md)** - Coin information API
- **[News Monitoring](integrations/NEWS_MONITORING.md)** - Real-time news tracking
- **[News Sources](integrations/NEWS_SOURCES.md)** - Available news sources
- **[Web Search](integrations/WEB_SEARCH.md)** - Web search capabilities

#### AI & Memory:
- **[OpenRouter Integration](integrations/OPENROUTER_INTEGRATION.md)** - AI model routing
  - [Caching](integrations/OPENROUTER_CACHING.md) - Prompt caching
  - [Models](integrations/OPENROUTER_MODELS.md) - Available models
- **[Mem0 Integration](integrations/MEM0_INTEGRATION.md)** - User memory management
- **[Session Persistence](integrations/SESSION_PERSISTENCE.md)** - Session management

**For third-party integrations** 🔌

---

### 7️⃣ [Tools](tools/)
Available tools and utilities.

- **[Get Price Tool](tools/GET_PRICE_TOOL.md)** - Real-time price fetching
- **[Tools Summary](tools/TOOLS_SUMMARY.md)** - All available tools

**For tool usage and development** 🛠️

---

### 8️⃣ [Development](development/)
Development guides and resources.

- **[Development Guide](development/DEVELOPMENT.md)** - Complete development workflow
- **[Implementation Checklist](development/IMPLEMENTATION_CHECKLIST.md)** - Feature tracking
- **[Mobile Data Requirements](development/MOBILE_DATA_REQUIREMENTS.md)** - Mobile app specs

**For contributors and developers** 💻

---

## 🎯 Common Use Cases

### I want to...

#### 🚀 Get Started Quickly
→ [Quick Start Guide](getting-started/QUICKSTART.md)

#### 📊 Integrate Real-time Market Data
→ [WebSocket Structure](websocket/WS_STRUCTURE.md)  
→ [Backpack Quick Start](websocket/BACKPACK_QUICKSTART.md)

#### 🤖 Build Custom AI Agents
→ [Agent Structure](agents/AGENTS_STRUCTURE.md)  
→ [Development Guide](development/DEVELOPMENT.md)

#### 🔧 Use the API
→ [API Reference](api/API_REFERENCE.md)

#### 🔌 Add New Integrations
→ [Development Guide](development/DEVELOPMENT.md)  
→ [Architecture](architecture/ARCHITECTURE.md)

#### 📈 Access Price Data
→ [Get Price Tool](tools/GET_PRICE_TOOL.md)  
→ [Data Sources](websocket/DATA_SOURCES.md)

#### 🗞️ Monitor Crypto News
→ [News Monitoring](integrations/NEWS_MONITORING.md)

#### 💾 Manage User Memory
→ [Mem0 Integration](integrations/MEM0_INTEGRATION.md)

---

## 📊 Documentation Statistics

- **Total Documents**: 30+
- **Categories**: 8
- **Code Examples**: 100+
- **Diagrams**: 10+
- **Last Updated**: 2026-04-16

---

## 🗺️ Documentation Map

```
docs/
├── README.md (You are here!)
├── DOCS_INDEX.md (Complete index)
│
├── getting-started/
│   ├── QUICKSTART.md
│   └── FEATURES.md
│
├── architecture/
│   ├── ARCHITECTURE.md
│   ├── PROJECT_SUMMARY.md
│   └── RESTRUCTURE_SUMMARY.md
│
├── api/
│   ├── API_REFERENCE.md
│   └── API_DOCUMENTATION.md
│
├── agents/
│   ├── AGENTS_STRUCTURE.md
│   ├── AGENTS_VISUAL.md
│   └── ASSISTANT_TYPES.md
│
├── websocket/
│   ├── WS_STRUCTURE.md
│   ├── DATA_SOURCES.md
│   ├── TRADING_ASSETS.md
│   ├── BACKPACK_INTEGRATION.md
│   ├── BACKPACK_QUICKSTART.md
│   └── BACKPACK_IMPLEMENTATION_SUMMARY.md
│
├── integrations/
│   ├── COINGECKO_INTEGRATION.md
│   ├── MEM0_INTEGRATION.md
│   ├── OPENROUTER_INTEGRATION.md
│   ├── OPENROUTER_CACHING.md
│   ├── OPENROUTER_MODELS.md
│   ├── NEWS_MONITORING.md
│   ├── NEWS_SOURCES.md
│   ├── WEB_SEARCH.md
│   └── SESSION_PERSISTENCE.md
│
├── tools/
│   ├── GET_PRICE_TOOL.md
│   └── TOOLS_SUMMARY.md
│
└── development/
    ├── DEVELOPMENT.md
    ├── IMPLEMENTATION_CHECKLIST.md
    └── MOBILE_DATA_REQUIREMENTS.md
```

---

## 🎓 Learning Paths

### 🌱 Beginner Path (1-2 hours)
1. [Quick Start](getting-started/QUICKSTART.md) - 15 min
2. [Features Overview](getting-started/FEATURES.md) - 30 min
3. [API Reference](api/API_REFERENCE.md) - 30 min
4. Try examples - 15 min

### 🌿 Intermediate Path (3-4 hours)
1. [Architecture](architecture/ARCHITECTURE.md) - 45 min
2. [Agent Structure](agents/AGENTS_STRUCTURE.md) - 30 min
3. [WebSocket Structure](websocket/WS_STRUCTURE.md) - 45 min
4. [Development Guide](development/DEVELOPMENT.md) - 60 min
5. Build something! - 60 min

### 🌳 Advanced Path (Full day)
1. Complete Intermediate Path
2. [All Integrations](integrations/) - 2 hours
3. [All Tools](tools/) - 1 hour
4. [Implementation Checklist](development/IMPLEMENTATION_CHECKLIST.md) - 30 min
5. Contribute to the project! - Rest of the day

---

## 🔍 Search Tips

### By Topic
- **Trading**: Check [WebSocket](websocket/) and [Tools](tools/)
- **AI Agents**: Check [Agents](agents/)
- **APIs**: Check [API Reference](api/)
- **Setup**: Check [Getting Started](getting-started/)
- **Development**: Check [Development](development/)

### By Integration
- **Backpack**: [websocket/BACKPACK_INTEGRATION.md](websocket/BACKPACK_INTEGRATION.md)
- **CoinGecko**: [integrations/COINGECKO_INTEGRATION.md](integrations/COINGECKO_INTEGRATION.md)
- **OpenRouter**: [integrations/OPENROUTER_INTEGRATION.md](integrations/OPENROUTER_INTEGRATION.md)
- **Mem0**: [integrations/MEM0_INTEGRATION.md](integrations/MEM0_INTEGRATION.md)

---

## 💡 Tips for Reading

1. **Start with Quick Start** - Get hands-on experience first
2. **Use the Index** - [DOCS_INDEX.md](DOCS_INDEX.md) has everything
3. **Follow Learning Paths** - Structured learning above
4. **Try Examples** - All docs have code examples
5. **Check Related Docs** - Links at bottom of each doc

---

## 🤝 Contributing to Documentation

Found an issue? Want to improve docs?

1. Check [Development Guide](development/DEVELOPMENT.md)
2. Follow documentation standards
3. Add examples for new features
4. Update this README if adding new sections

---

## 📞 Getting Help

### Documentation Issues
- **Outdated info?** Open an issue
- **Need clarification?** Ask in discussions
- **Want to contribute?** Submit a PR

### Code Issues
- Check [Development Guide](development/DEVELOPMENT.md)
- Check [Quick Start](getting-started/QUICKSTART.md)
- Check [API Reference](api/API_REFERENCE.md)

---

## 🎉 Quick Links

### Most Popular Docs
1. [Quick Start Guide](getting-started/QUICKSTART.md)
2. [API Reference](api/API_REFERENCE.md)
3. [WebSocket Structure](websocket/WS_STRUCTURE.md)
4. [Backpack Integration](websocket/BACKPACK_INTEGRATION.md)
5. [Development Guide](development/DEVELOPMENT.md)

### Latest Additions
- ✨ [Backpack Exchange Integration](websocket/BACKPACK_INTEGRATION.md) - NEW!
- ✨ [Backpack Quick Start](websocket/BACKPACK_QUICKSTART.md) - NEW!
- 🔄 [WebSocket Structure](websocket/WS_STRUCTURE.md) - Updated!

---

## 📈 Documentation Roadmap

### ✅ Completed
- Complete documentation structure
- All major features documented
- Code examples for all features
- Quick start guides
- API reference

### 🚧 In Progress
- Video tutorials
- Interactive examples
- More diagrams

### 📋 Planned
- FAQ section
- Troubleshooting guide
- Deployment guide
- Performance tuning guide

---

**Last Updated**: 2026-04-16  
**Version**: 2.0.0  
**Maintained by**: Rabit Backend Team

---

<div align="center">

### Ready to start? 🚀

**[Begin with Quick Start →](getting-started/QUICKSTART.md)**

or

**[Explore All Docs →](DOCS_INDEX.md)**

</div>
