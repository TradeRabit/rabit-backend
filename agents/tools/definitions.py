"""Tool definitions and models"""
from typing import Optional, Any, Callable, List
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Tool parameter definition"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolDefinition(BaseModel):
    """Tool definition with schema"""
    name: str
    description: str
    parameters: List[ToolParameter]
    function: Optional[Callable] = Field(default=None, exclude=True)


class ToolResult(BaseModel):
    """Tool execution result"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_details: Optional[dict] = None
