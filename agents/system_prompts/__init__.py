"""System prompts for agents"""
from pathlib import Path

def load_prompt(prompt_name: str) -> str:
    """
    Load system prompt from file
    
    Args:
        prompt_name: Name of prompt file (without .txt extension)
        
    Returns:
        Prompt content as string
    """
    prompt_file = Path(__file__).parent / f"{prompt_name}.txt"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_name}.txt")
    
    return prompt_file.read_text(encoding='utf-8')


def get_trading_agent_prompt() -> str:
    """Get trading agent system prompt"""
    return load_prompt("trading_agent")


def get_analysis_agent_prompt() -> str:
    """Get analysis agent system prompt"""
    return load_prompt("analysis_agent")


def get_risk_management_prompt() -> str:
    """Get risk management system prompt"""
    return load_prompt("risk_management")


__all__ = [
    "load_prompt",
    "get_trading_agent_prompt",
    "get_analysis_agent_prompt",
    "get_risk_management_prompt"
]
