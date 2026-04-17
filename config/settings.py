"""Application settings and configuration"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings"""
    
    # Claude API
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    
    # OpenRouter Configuration (optional)
    USE_OPENROUTER = os.getenv("USE_OPENROUTER", "false").lower() == "true"
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api")
    
    # Drift Protocol
    DRIFT_RPC_URL = os.getenv("DRIFT_RPC_URL", "https://api.mainnet-beta.solana.com")
    DRIFT_PROGRAM_ID = os.getenv("DRIFT_PROGRAM_ID", "dRiftyHA39MWEi3m9aunc5MzRF1JYJjb5ciH7N27eNn")
    
    # WebSocket
    WS_HOST = os.getenv("WS_HOST", "0.0.0.0")
    WS_PORT = int(os.getenv("WS_PORT", "8000"))
    
    # Trading Assets (used by all WS sources)
    TRADING_ASSETS = os.getenv("TRADING_ASSETS", "BTC,ETH,SOL,DOGE,BNB,SUI,APT,ARB,RENDER,XRP,INJ,LINK,PYTH,JTO,AVAX,WIF,JUP,TAO,KMNO,TNSR,DRIFT,RAY,HYPE,LTC,FARTCOIN").split(",")
    
    # Drift WebSocket
    DRIFT_WS_URL = os.getenv("DRIFT_WS_URL", "wss://data.api.drift.trade/ws")
    DRIFT_DLOB_WS_URL = os.getenv("DRIFT_DLOB_WS_URL", "wss://dlob.drift.trade/ws")
    DRIFT_SUBSCRIBE_ASSETS = int(os.getenv("DRIFT_SUBSCRIBE_ASSETS", "25"))
    # Use TRADING_ASSETS for Drift (backward compatibility)
    DRIFT_ASSETS = TRADING_ASSETS
    
    # Backpack Exchange
    BACKPACK_WS_URL = os.getenv("BACKPACK_WS_URL", "wss://ws.backpack.exchange")
    BACKPACK_ENABLED = os.getenv("BACKPACK_ENABLED", "true").lower() == "true"
    BACKPACK_QUOTE_ASSET = os.getenv("BACKPACK_QUOTE_ASSET", "USDC")  # SOL_USDC, BTC_USDC
    BACKPACK_SUBSCRIBE_ASSETS = int(os.getenv("BACKPACK_SUBSCRIBE_ASSETS", "25"))
    
    # Price Source Selection
    PRICE_SOURCE = os.getenv("PRICE_SOURCE", "backpack")  # "drift", "backpack", or "both"
    
    # Binance Configuration
    BINANCE_API_URL = os.getenv("BINANCE_API_URL", "https://api.binance.com")
    BINANCE_WS_URL = os.getenv("BINANCE_WS_URL", "wss://stream.binance.com:9443/ws")
    BINANCE_OHLC_INTERVAL = os.getenv("BINANCE_OHLC_INTERVAL", "1h")
    BINANCE_OHLC_DOWNLOAD_LIMIT = int(os.getenv("BINANCE_OHLC_DOWNLOAD_LIMIT", "100"))
    
    # Data Configuration
    WS_DATA_FIELDS = os.getenv("WS_DATA_FIELDS", "price,change_24h,volume_24h,open_interest,funding_rate").split(",")
    OHLC_ENABLED = os.getenv("OHLC_ENABLED", "true").lower() == "true"
    OHLC_HISTORY_ENABLED = os.getenv("OHLC_HISTORY_ENABLED", "true").lower() == "true"
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"

    # Agent Uploads
    AGENT_UPLOAD_DIR = Path(os.getenv("AGENT_UPLOAD_DIR", "data/uploads/tmp"))
    AGENT_UPLOAD_TTL_SECONDS = int(os.getenv("AGENT_UPLOAD_TTL_SECONDS", "3600"))
    AGENT_UPLOAD_MAX_SIZE_MB = int(os.getenv("AGENT_UPLOAD_MAX_SIZE_MB", "10"))
    
    # Mem0 Configuration
    MEM0_ENABLED = os.getenv("MEM0_ENABLED", "true").lower() == "true"
    MEMORY_TOOLS_ENABLED = os.getenv("MEMORY_TOOLS_ENABLED", "true").lower() == "true"
    MEM0_HOST = os.getenv("MEM0_HOST", "localhost")
    MEM0_PORT = int(os.getenv("MEM0_PORT", "8080"))
    MEM0_URL = os.getenv("MEM0_URL", "").strip() or f"http://{MEM0_HOST}:{MEM0_PORT}"
    MEM0_API_KEY = os.getenv("MEM0_API_KEY", "")

    # Tool feature gates
    WEB_SEARCH_ENABLED = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"
    
    # SearXNG Configuration (Not used - using DuckDuckGo instead)
    SEARXNG_ENABLED = os.getenv("SEARXNG_ENABLED", "false").lower() == "true"
    SEARXNG_URL = os.getenv("SEARXNG_URL", "http://localhost:8888")

    def get_price_sources(self) -> list[str]:
        """
        Resolve PRICE_SOURCE into concrete WebSocket sources.

        Supported values:
        - "backpack"
        - "drift"
        - "both" -> backpack + drift
        """
        price_source = (self.PRICE_SOURCE or "backpack").strip().lower()

        if price_source == "both":
            sources = ["backpack", "drift"]
        elif price_source in {"backpack", "drift"}:
            sources = [price_source]
        else:
            sources = ["backpack"]

        if "backpack" in sources and not self.BACKPACK_ENABLED:
            sources = [source for source in sources if source != "backpack"]

        return sources

    def uses_price_source(self, source: str) -> bool:
        """Check if a source is enabled by PRICE_SOURCE."""
        return source.strip().lower() in self.get_price_sources()


settings = Settings()
