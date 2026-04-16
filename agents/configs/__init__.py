"""Agent configurations"""
from typing import Dict, Any
from pathlib import Path
import json

def load_config(config_name: str) -> Dict[str, Any]:
    """
    Load agent configuration from JSON file
    
    Args:
        config_name: Name of config file (without .json extension)
        
    Returns:
        Configuration dictionary
    """
    config_file = Path(__file__).parent / f"{config_name}.json"
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_name}.json")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_trading_agent_config() -> Dict[str, Any]:
    """Get trading agent configuration"""
    return load_config("trading_agent")


def get_default_tools() -> Dict[str, Any]:
    """Get default tools configuration"""
    return load_config("default_tools")


__all__ = [
    "load_config",
    "get_trading_agent_config",
    "get_default_tools"
]
