"""Claude Agent implementations"""
from agents.core import BaseAgent, TradingAgent
from agents.memory import ConversationMemory, Message, ConversationDatabase, get_conversation_database
from agents.compression import ConversationCompressor
from agents.tools import ToolRegistry, ToolDefinition, ToolParameter, ToolResult, tool_registry
from agents.examples import register_trading_tools
from agents.openrouter import OpenRouterModels, ModelInfo, get_openrouter_models, ModelsDatabase, get_models_database

__all__ = [
    # Core
    "BaseAgent",
    "TradingAgent",
    # Memory
    "ConversationMemory",
    "Message",
    "ConversationDatabase",
    "get_conversation_database",
    # Compression
    "ConversationCompressor",
    # Tools
    "ToolRegistry",
    "ToolDefinition",
    "ToolParameter",
    "ToolResult",
    "tool_registry",
    # Trading Tools
    "register_trading_tools",
    # OpenRouter
    "OpenRouterModels",
    "ModelInfo",
    "get_openrouter_models",
    "ModelsDatabase",
    "get_models_database"
]
