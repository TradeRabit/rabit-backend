from agents.core.trading_agent import TradingAgent
from agents.system_prompts import get_trading_agent_prompt


def test_trading_agent_uses_prompt_loader(monkeypatch):
    monkeypatch.setattr("agents.core.base.Anthropic", lambda *args, **kwargs: object())
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: object())

    agent = TradingAgent(scope_id="scope-1", user_id="user-1")

    assert agent.system_prompt == get_trading_agent_prompt()
    assert "Rabit Agent" in agent.system_prompt
    assert "English by default" in agent.system_prompt
    assert "show_hint" in agent.system_prompt
    assert "Respect Conversation Style" in agent.system_prompt
    assert "Respect Trading Style" in agent.system_prompt
