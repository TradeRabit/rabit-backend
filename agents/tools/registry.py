"""Tool registry implementation"""
from typing import Dict, Any, List, Optional
from utils.logger import get_logger
from .definitions import ToolDefinition, ToolResult

logger = get_logger(__name__)


class ToolRegistry:
    """Registry for agent tools"""
    
    def __init__(self):
        """Initialize tool registry"""
        self._tools: Dict[str, ToolDefinition] = {}
    
    def register(self, tool: ToolDefinition):
        """
        Register a tool
        
        Args:
            tool: Tool definition to register
        """
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """
        Get tool by name
        
        Args:
            name: Tool name
            
        Returns:
            Tool definition or None
        """
        return self._tools.get(name)
    
    def list_tools(self) -> List[ToolDefinition]:
        """
        List all registered tools
        
        Returns:
            List of tool definitions
        """
        return list(self._tools.values())
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        Get tools schema for Claude API
        
        Returns:
            List of tool schemas
        """
        schemas = []
        for tool in self._tools.values():
            schema = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            
            for param in tool.parameters:
                schema["input_schema"]["properties"][param.name] = {
                    "type": param.type,
                    "description": param.description
                }
                
                if param.required:
                    schema["input_schema"]["required"].append(param.name)
            
            schemas.append(schema)
        
        return schemas
    
    async def execute(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        Execute a tool with detailed error handling
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool execution result with detailed error info
        """
        tool = self.get_tool(name)
        
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found",
                error_details={
                    "available_tools": [t.name for t in self.list_tools()],
                    "suggestion": "Check available tools and use the correct tool name"
                }
            )
        
        if not tool.function:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' has no implementation",
                error_details={
                    "tool_name": name,
                    "suggestion": "This tool is registered but not implemented yet"
                }
            )
        
        # Validate parameters
        validation_result = self._validate_parameters(tool, arguments)
        if not validation_result["valid"]:
            return ToolResult(
                success=False,
                error="Invalid parameters provided",
                error_details={
                    "tool_name": name,
                    "validation_errors": validation_result["errors"],
                    "expected_parameters": [
                        {
                            "name": p.name,
                            "type": p.type,
                            "required": p.required,
                            "description": p.description
                        }
                        for p in tool.parameters
                    ],
                    "provided_parameters": list(arguments.keys()),
                    "suggestion": "Check parameter names, types, and required fields"
                }
            )
        
        # Execute tool
        try:
            result = await tool.function(**arguments)
            return ToolResult(
                success=True,
                data=result
            )
        except TypeError as e:
            return ToolResult(
                success=False,
                error=f"Parameter type error: {str(e)}",
                error_details={
                    "tool_name": name,
                    "error_type": "TypeError",
                    "provided_arguments": arguments,
                    "expected_parameters": [
                        {
                            "name": p.name,
                            "type": p.type,
                            "description": p.description
                        }
                        for p in tool.parameters
                    ],
                    "suggestion": "Ensure all parameters match the expected types"
                }
            )
        except Exception as e:
            logger.error(f"Tool execution error: {name} - {str(e)}")
            return ToolResult(
                success=False,
                error=f"Execution error: {str(e)}",
                error_details={
                    "tool_name": name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "suggestion": "Check the error message and adjust parameters accordingly"
                }
            )
    
    def _validate_parameters(self, tool: ToolDefinition, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate tool parameters
        
        Args:
            tool: Tool definition
            arguments: Provided arguments
            
        Returns:
            Validation result with errors
        """
        errors = []
        
        # Check required parameters
        for param in tool.parameters:
            if param.required and param.name not in arguments:
                errors.append({
                    "parameter": param.name,
                    "error": "Required parameter missing",
                    "type": param.type,
                    "description": param.description
                })
        
        # Check for unexpected parameters
        expected_params = {p.name for p in tool.parameters}
        for arg_name in arguments.keys():
            if arg_name not in expected_params:
                errors.append({
                    "parameter": arg_name,
                    "error": "Unexpected parameter",
                    "suggestion": f"Expected parameters: {', '.join(expected_params)}"
                })
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


# Global tool registry instance
tool_registry = ToolRegistry()
