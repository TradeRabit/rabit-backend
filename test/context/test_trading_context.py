"""
Tests for Trading Context Management
"""

import pytest
from datetime import datetime
from agents.context import (
    TradingContext,
    get_trading_context,
    set_trading_context,
    update_exchange,
    update_asset,
    update_mode,
    clear_trading_context,
    get_context_for_agent
)


class TestTradingContext:
    """Test TradingContext dataclass"""
    
    def setup_method(self):
        """Clear context before each test"""
        clear_trading_context()
    
    def test_create_context(self):
        """Test creating a trading context"""
        context = TradingContext(
            exchange="drift",
            asset="BTC",
            mode="asset_locked"
        )
        
        assert context.exchange == "drift"
        assert context.asset == "BTC"
        assert context.mode == "asset_locked"
        assert context.updated_at is not None
    
    def test_context_to_dict(self):
        """Test converting context to dictionary"""
        context = TradingContext(
            exchange="backpack",
            asset="ETH",
            mode="global"
        )
        
        data = context.to_dict()
        assert data["exchange"] == "backpack"
        assert data["asset"] == "ETH"
        assert data["mode"] == "global"
        assert "updated_at" in data
    
    def test_context_summary_asset_locked(self):
        """Test context summary for asset-locked mode"""
        context = TradingContext(
            exchange="drift",
            asset="SOL",
            mode="asset_locked"
        )
        
        summary = context.get_context_summary()
        assert "SOL" in summary
        assert "DRIFT" in summary
        assert "Asset-Locked" in summary
    
    def test_context_summary_global(self):
        """Test context summary for global mode"""
        context = TradingContext(
            exchange="backpack",
            mode="global"
        )
        
        summary = context.get_context_summary()
        assert "BACKPACK" in summary
        assert "Global Mode" in summary


class TestContextManagement:
    """Test context management functions"""
    
    def setup_method(self):
        """Clear context before each test"""
        clear_trading_context()
    
    def test_set_global_context(self):
        """Test setting global trading context"""
        context = set_trading_context(
            exchange="drift",
            mode="global"
        )
        
        assert context.exchange == "drift"
        assert context.asset is None
        assert context.mode == "global"
        
        # Verify it's stored globally
        stored = get_trading_context()
        assert stored is not None
        assert stored.exchange == "drift"
    
    def test_set_asset_locked_context(self):
        """Test setting asset-locked trading context"""
        context = set_trading_context(
            exchange="backpack",
            asset="BTC",
            mode="asset_locked"
        )
        
        assert context.exchange == "backpack"
        assert context.asset == "BTC"
        assert context.mode == "asset_locked"
    
    def test_set_asset_locked_without_asset_raises_error(self):
        """Test that asset-locked mode requires asset"""
        with pytest.raises(ValueError, match="Asset is required"):
            set_trading_context(
                exchange="drift",
                mode="asset_locked"
            )
    
    def test_asset_normalization(self):
        """Test that asset symbols are normalized to uppercase"""
        context = set_trading_context(
            exchange="drift",
            asset="btc",  # lowercase
            mode="asset_locked"
        )
        
        assert context.asset == "BTC"  # Should be uppercase
    
    def test_update_exchange(self):
        """Test updating only the exchange"""
        # Set initial context
        set_trading_context(exchange="drift", asset="BTC", mode="asset_locked")
        
        # Update exchange
        context = update_exchange("backpack")
        
        assert context.exchange == "backpack"
        assert context.asset == "BTC"  # Should be preserved
        assert context.mode == "asset_locked"  # Should be preserved
    
    def test_update_asset(self):
        """Test updating only the asset"""
        # Set initial context
        set_trading_context(exchange="drift", asset="BTC", mode="global")
        
        # Update asset
        context = update_asset("ETH")
        
        assert context.exchange == "drift"  # Should be preserved
        assert context.asset == "ETH"
        assert context.mode == "global"  # Should be preserved
    
    def test_update_mode_to_global(self):
        """Test switching to global mode"""
        # Set initial context
        set_trading_context(exchange="drift", asset="BTC", mode="asset_locked")
        
        # Switch to global
        context = update_mode("global")
        
        assert context.mode == "global"
        assert context.asset == "BTC"  # Asset is preserved but not required
    
    def test_update_mode_to_asset_locked_without_asset_raises_error(self):
        """Test that switching to asset-locked requires asset"""
        # Set global context without asset
        set_trading_context(exchange="drift", mode="global")
        
        # Try to switch to asset-locked
        with pytest.raises(ValueError, match="Cannot switch to asset_locked"):
            update_mode("asset_locked")
    
    def test_clear_context(self):
        """Test clearing trading context"""
        # Set context
        set_trading_context(exchange="drift", asset="BTC", mode="asset_locked")
        assert get_trading_context() is not None
        
        # Clear context
        clear_trading_context()
        assert get_trading_context() is None
    
    def test_get_context_for_agent_with_context(self):
        """Test getting formatted context string for agent"""
        set_trading_context(
            exchange="drift",
            asset="BTC",
            mode="asset_locked"
        )
        
        context_str = get_context_for_agent()
        
        assert "CURRENT TRADING CONTEXT" in context_str
        assert "DRIFT" in context_str
        assert "BTC" in context_str
        assert "Asset Locked" in context_str
    
    def test_get_context_for_agent_without_context(self):
        """Test getting context string when no context is set"""
        clear_trading_context()
        
        context_str = get_context_for_agent()
        
        assert "No trading context set" in context_str
    
    def test_get_context_for_agent_global_mode(self):
        """Test context string for global mode"""
        set_trading_context(exchange="backpack", mode="global")
        
        context_str = get_context_for_agent()
        
        assert "BACKPACK" in context_str
        assert "Global Mode" in context_str
        assert "All assets available" in context_str


class TestContextScenarios:
    """Test real-world usage scenarios"""
    
    def setup_method(self):
        """Clear context before each test"""
        clear_trading_context()
    
    def test_scenario_home_to_assist_global(self):
        """
        Scenario: User on home page → navigates to Assist
        Expected: Global mode, can trade any asset
        """
        # User selects Drift exchange on home page
        context = set_trading_context(exchange="drift", mode="global")
        
        assert context.mode == "global"
        assert context.asset is None
        
        # Agent can now trade any asset
        summary = context.get_context_summary()
        assert "All Assets" in summary
    
    def test_scenario_asset_detail_to_assist_locked(self):
        """
        Scenario: User on BTC detail page → clicks "Trade Now"
        Expected: Asset-locked mode, only BTC
        """
        # User clicks "Trade Now" on BTC detail page
        context = set_trading_context(
            exchange="drift",
            asset="BTC",
            mode="asset_locked"
        )
        
        assert context.mode == "asset_locked"
        assert context.asset == "BTC"
        
        # Agent is locked to BTC
        summary = context.get_context_summary()
        assert "BTC" in summary
        assert "Asset-Locked" in summary
    
    def test_scenario_switch_exchange(self):
        """
        Scenario: User switches from Drift to Backpack
        Expected: Exchange changes, other context preserved
        """
        # Initial: Trading BTC on Drift
        set_trading_context(
            exchange="drift",
            asset="BTC",
            mode="asset_locked"
        )
        
        # User switches to Backpack
        context = update_exchange("backpack")
        
        assert context.exchange == "backpack"
        assert context.asset == "BTC"  # Preserved
        assert context.mode == "asset_locked"  # Preserved
    
    def test_scenario_switch_asset_in_global_mode(self):
        """
        Scenario: User in global mode, switches between assets
        Expected: Asset updates freely
        """
        # Start in global mode
        set_trading_context(exchange="drift", mode="global")
        
        # User asks about BTC
        update_asset("BTC")
        context = get_trading_context()
        assert context.asset == "BTC"
        
        # User asks about ETH
        update_asset("ETH")
        context = get_trading_context()
        assert context.asset == "ETH"
        
        # Still in global mode
        assert context.mode == "global"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
