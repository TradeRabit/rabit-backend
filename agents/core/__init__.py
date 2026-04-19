"""Core agent implementations"""
from .base import BaseAgent
from .trading_agent import TradingAgent
from agents.pipeline.pipeline import (
    AgentPipelineStage,
    AgentPipelineTrace,
    build_pipeline_trace,
    resolve_specialist_target,
)

__all__ = [
    "AgentPipelineStage",
    "AgentPipelineTrace",
    "BaseAgent",
    "TradingAgent",
    "build_pipeline_trace",
    "resolve_specialist_target",
]
