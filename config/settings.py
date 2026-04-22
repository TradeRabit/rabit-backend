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
    OPENROUTER_SESSION_COST_DB_PATH = os.getenv(
        "OPENROUTER_SESSION_COST_DB_PATH",
        "data/openrouter_session_costs.json",
    )
    MONITORING_COST_DB_PATH = os.getenv(
        "MONITORING_COST_DB_PATH",
        "data/monitoring_costs.json",
    )
    ALERT_SETUP_COST_USD = float(os.getenv("ALERT_SETUP_COST_USD", "0.001"))
    MONITORING_COST_PER_SYMBOL_HOUR_USD = float(
        os.getenv("MONITORING_COST_PER_SYMBOL_HOUR_USD", "0.002")
    )
    ALERT_TRIGGER_COST_USD = float(os.getenv("ALERT_TRIGGER_COST_USD", "0.0005"))
    
    # WebSocket
    WS_HOST = os.getenv("WS_HOST", "0.0.0.0")
    WS_PORT = int(os.getenv("WS_PORT", "8000"))
    
    # Trading Assets (used by all WS sources)
    TRADING_ASSETS = os.getenv("TRADING_ASSETS", "BTC,ETH,SOL,DOGE,BNB,SUI,APT,ARB,RENDER,XRP,INJ,LINK,PYTH,JTO,AVAX,WIF,JUP,TAO,KMNO,TNSR,DRIFT,RAY,HYPE,LTC,FARTCOIN").split(",")
    
    # Phantom market data surface backed by Hyperliquid
    PHANTOM_ENABLED = os.getenv("PHANTOM_ENABLED", "true").lower() == "true"
    PHANTOM_PRICE_POLL_INTERVAL_SECONDS = float(
        os.getenv("PHANTOM_PRICE_POLL_INTERVAL_SECONDS", "5")
    )
    HYPERLIQUID_API_URL = os.getenv("HYPERLIQUID_API_URL", "https://api.hyperliquid.xyz")
    HYPERLIQUID_WS_URL = os.getenv("HYPERLIQUID_WS_URL", "wss://api.hyperliquid.xyz/ws")
    HYPERLIQUID_DEX = os.getenv("HYPERLIQUID_DEX", "").strip()
    PRICE_SOURCE = os.getenv("PRICE_SOURCE", "phantom")
    
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
    AGENT_PIPELINE_ARTIFACTS_DB_PATH = os.getenv(
        "AGENT_PIPELINE_ARTIFACTS_DB_PATH",
        "data/agent_pipeline_artifacts.json",
    )
    AGENT_PIPELINE_ARTIFACT_TTL_SECONDS = int(
        os.getenv("AGENT_PIPELINE_ARTIFACT_TTL_SECONDS", "604800")
    )
    
    # Mem0 Configuration
    MEM0_ENABLED = os.getenv("MEM0_ENABLED", "true").lower() == "true"
    MEMORY_TOOLS_ENABLED = os.getenv("MEMORY_TOOLS_ENABLED", "true").lower() == "true"
    MEM0_HOST = os.getenv("MEM0_HOST", "localhost")
    MEM0_PORT = int(os.getenv("MEM0_PORT", "8080"))
    MEM0_URL = os.getenv("MEM0_URL", "").strip() or f"http://{MEM0_HOST}:{MEM0_PORT}"
    MEM0_API_KEY = os.getenv("MEM0_API_KEY", "")

    # Tool feature gates
    WEB_SEARCH_ENABLED = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"
    NEWS_IS_NEW_WINDOW_SECONDS = int(
        os.getenv("NEWS_IS_NEW_WINDOW_SECONDS", "86400")
    )
    TRADE_DEBRIEF_DB_PATH = os.getenv(
        "TRADE_DEBRIEF_DB_PATH",
        "data/trade_debriefs.json",
    )
    USER_PROFILES_DB_PATH = os.getenv(
        "USER_PROFILES_DB_PATH",
        "data/user_profiles.json",
    )

    # Rabit on-chain contract
    RABIT_CONTRACT_CLUSTER = os.getenv("RABIT_CONTRACT_CLUSTER", "devnet").strip().lower()
    RABIT_CONTRACT_RPC_URL = os.getenv("RABIT_CONTRACT_RPC_URL", "").strip()
    RABIT_CONTRACT_PROGRAM_ID = os.getenv("RABIT_CONTRACT_PROGRAM_ID", "").strip()
    RABIT_AI_USAGE_PAYMENT_MINT = os.getenv("RABIT_AI_USAGE_PAYMENT_MINT", "").strip()
    RABIT_AI_USAGE_PAYMENT_TOKEN_SYMBOL = os.getenv("RABIT_AI_USAGE_PAYMENT_TOKEN_SYMBOL", "USDC").strip() or "USDC"
    RABIT_AI_USAGE_PAYMENT_MINT_DECIMALS = int(
        os.getenv("RABIT_AI_USAGE_PAYMENT_MINT_DECIMALS", "6")
    )
    RABIT_AI_USAGE_PAYMENT_TOKEN_USD_PRICE = float(
        os.getenv("RABIT_AI_USAGE_PAYMENT_TOKEN_USD_PRICE", "1.0")
    )
    RABIT_AI_USAGE_PLATFORM_FEE_BPS = int(
        os.getenv("RABIT_AI_USAGE_PLATFORM_FEE_BPS", "500")
    )
    RABIT_AI_USAGE_DEFAULT_MARKUP_BPS = int(
        os.getenv("RABIT_AI_USAGE_DEFAULT_MARKUP_BPS", "500")
    )
    RABIT_AI_USAGE_DEFAULT_USAGE_TYPE = (
        os.getenv("RABIT_AI_USAGE_DEFAULT_USAGE_TYPE", "text").strip().lower() or "text"
    )
    RABIT_AI_USAGE_CHAT_MIN_BALANCE_USD = float(
        os.getenv("RABIT_AI_USAGE_CHAT_MIN_BALANCE_USD", "1.0")
    )
    RABIT_AI_USAGE_ENFORCE_CHAT_BALANCE = os.getenv(
        "RABIT_AI_USAGE_ENFORCE_CHAT_BALANCE",
        "true",
    ).lower() == "true"
    RABIT_AI_USAGE_DELEGATION_EXPIRY_SECONDS = int(
        os.getenv("RABIT_AI_USAGE_DELEGATION_EXPIRY_SECONDS", "2592000")
    )
    RABIT_AI_USAGE_DELEGATION_SPENDING_LIMIT_UNITS = int(
        os.getenv("RABIT_AI_USAGE_DELEGATION_SPENDING_LIMIT_UNITS", "1000000000")
    )
    RABIT_CONTRACT_BACKEND_SIGNER = os.getenv("RABIT_CONTRACT_BACKEND_SIGNER", "").strip()
    RABIT_AI_USAGE_SETTLEMENTS_DB_PATH = os.getenv(
        "RABIT_AI_USAGE_SETTLEMENTS_DB_PATH",
        "data/ai_usage_settlements.json",
    )

    # Mobile wallet auth
    AUTH_JWT_SECRET = os.getenv("AUTH_JWT_SECRET", "").strip()
    AUTH_JWT_ISSUER = os.getenv("AUTH_JWT_ISSUER", "rabit-backend")
    AUTH_JWT_AUDIENCE = os.getenv("AUTH_JWT_AUDIENCE", "rabit-mobile")
    AUTH_JWT_TTL_SECONDS = int(os.getenv("AUTH_JWT_TTL_SECONDS", "604800"))
    WALLET_AUTH_NONCE_DB_PATH = os.getenv(
        "WALLET_AUTH_NONCE_DB_PATH",
        "data/wallet_auth_nonces.json",
    )
    WALLET_AUTH_NONCE_TTL_SECONDS = int(os.getenv("WALLET_AUTH_NONCE_TTL_SECONDS", "300"))
    
    # SearXNG Configuration (Not used - using DuckDuckGo instead)
    SEARXNG_ENABLED = os.getenv("SEARXNG_ENABLED", "false").lower() == "true"
    SEARXNG_URL = os.getenv("SEARXNG_URL", "http://localhost:8888")

    def get_price_sources(self) -> list[str]:
        """
        Resolve PRICE_SOURCE into concrete WebSocket sources.

        Supported values:
        - "phantom"
        """
        price_source = (self.PRICE_SOURCE or "phantom").strip().lower()
        sources = ["phantom"] if price_source == "phantom" else []

        if "phantom" in sources and not self.PHANTOM_ENABLED:
            sources = [source for source in sources if source != "phantom"]

        return sources

    def uses_price_source(self, source: str) -> bool:
        """Check if a source is enabled by PRICE_SOURCE."""
        return source.strip().lower() in self.get_price_sources()


settings = Settings()
