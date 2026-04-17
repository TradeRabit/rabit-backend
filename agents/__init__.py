"""
Rabit Trading Agent System

This package contains the core agent system including:
- Agent implementations (core/)
- Tool registry (tools_registry/)
- System prompts (system_prompts/)
- Agent configurations (configs/)
- Memory management (memory/)
- Compression utilities (compression/)
- OpenRouter integration (openrouter/)
- Trading context (context/)
"""

# Core imports
from agents.core import TradingAgent, BaseAgent
from agents.compression import ConversationCompressor
from agents.tools import ToolRegistry, ToolDefinition, ToolParameter, ToolResult, tool_registry
from agents.tools_registry import register_trading_tools
from agents.openrouter import OpenRouterModels, ModelInfo, get_openrouter_models, ModelsDatabase, get_models_database
from agents.uploads import (
    AgentAttachment,
    UploadedFileRecord,
    TemporaryUploadManager,
    UploadValidationError,
    get_upload_manager,
)

# System prompts
from agents.system_prompts import (
    load_prompt,
    get_trading_agent_prompt,
    get_analysis_agent_prompt,
    get_risk_management_prompt
)

# Configurations
from agents.configs import (
    load_config,
    get_trading_agent_config,
    get_default_tools
)

# Trading context
from agents.context import (
    TradingContext,
    ExchangeType,
    TradingMode,
    get_trading_context,
    set_trading_context,
    update_exchange,
    update_asset,
    update_mode,
    clear_trading_context,
    get_context_for_agent
)
from agents.memory import Mem0Error, Mem0DisabledError, Mem0RequestError, get_mem0_client

__version__ = "1.0.0"

__all__ = [
    # Core
    "TradingAgent",
    "BaseAgent",
    "ConversationCompressor",
    
    # Tools
    "ToolRegistry",
    "ToolDefinition",
    "ToolParameter",
    "ToolResult",
    "tool_registry",
    "register_trading_tools",
    
    # OpenRouter
    "OpenRouterModels",
    "ModelInfo",
    "get_openrouter_models",
    "ModelsDatabase",
    "get_models_database",

    # Uploads
    "AgentAttachment",
    "UploadedFileRecord",
    "TemporaryUploadManager",
    "UploadValidationError",
    "get_upload_manager",
    "Mem0Error",
    "Mem0DisabledError",
    "Mem0RequestError",
    "get_mem0_client",
    
    # System Prompts
    "load_prompt",
    "get_trading_agent_prompt",
    "get_analysis_agent_prompt",
    "get_risk_management_prompt",
    
    # Configurations
    "load_config",
    "get_trading_agent_config",
    "get_default_tools",
    
    # Trading Context
    "TradingContext",
    "ExchangeType",
    "TradingMode",
    "get_trading_context",
    "set_trading_context",
    "update_exchange",
    "update_asset",
    "update_mode",
    "clear_trading_context",
    "get_context_for_agent"
]
