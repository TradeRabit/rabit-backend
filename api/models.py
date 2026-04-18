"""
API Response Models
Pydantic models untuk API responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AssetListItem(BaseModel):
    """Asset item in list"""
    symbol: str = Field(..., description="Asset symbol (e.g., 'BTC')")
    name: str = Field(..., description="Asset name (e.g., 'Bitcoin')")
    price: float = Field(..., description="Current price")
    change_24h: Optional[float] = Field(None, description="24h price change percentage")
    categories: List[str] = Field(default_factory=list, description="Asset categories")


class AssetListResponse(BaseModel):
    """Response for GET /api/assets"""
    assets: List[AssetListItem]
    total: int = Field(..., description="Total number of assets")


class AssetLinks(BaseModel):
    """Asset links"""
    website: Optional[str] = None
    twitter: Optional[str] = None
    telegram: Optional[str] = None
    github: Optional[str] = None
    explorer: Optional[str] = None
    contract_address: Optional[str] = None


class AssetDetailResponse(BaseModel):
    """Response for GET /api/assets/{symbol}"""
    # Basic info
    symbol: str
    name: str
    
    # Price data
    price: float
    change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    
    # Market data (futures)
    market_cap: Optional[float] = None
    fdv: Optional[float] = None
    open_interest: Optional[float] = None
    funding_rate: Optional[float] = None
    
    # Static info
    description: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    links: AssetLinks
    
    # Metadata
    last_updated: str


class OHLCData(BaseModel):
    """OHLC candle data"""
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    open: float
    high: float
    low: float
    close: float
    volume: float


class OHLCResponse(BaseModel):
    """Response for GET /api/assets/{symbol}/ohlc"""
    symbol: str
    interval: str
    data: List[OHLCData]


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str = Field(..., description="Error message")



class ModelInfoResponse(BaseModel):
    """OpenRouter model information"""
    id: str
    name: str
    provider: str
    description: Optional[str] = None
    context_length: int
    input_price: float = Field(..., description="Input price per 1M tokens (USD)")
    output_price: float = Field(..., description="Output price per 1M tokens (USD)")
    supports_tools: bool
    supports_reasoning: bool
    knowledge_cutoff: Optional[str] = None
    created: Optional[int] = None
    modality: Optional[str] = None
    tokenizer: Optional[str] = None
    enabled: bool


class ModelsListResponse(BaseModel):
    """Response for GET /api/models"""
    models: List[ModelInfoResponse]
    total: int
    enabled: int
    disabled: int
    last_updated: Optional[str] = None


class ModelStatsResponse(BaseModel):
    """Model statistics"""
    total_models: int
    enabled_models: int
    disabled_models: int
    models_with_tools: int
    models_with_reasoning: int
    providers: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Statistics grouped by provider")
    last_updated: Optional[str] = None


class ModelToggleRequest(BaseModel):
    """Request to enable/disable model"""
    model_id: str
    enabled: bool


class AgentUploadResponse(BaseModel):
    """Response for agent temporary uploads."""

    file_id: str
    filename: str
    content_type: str
    kind: str
    size_bytes: int
    expires_at: datetime


class AgentUploadDeleteResponse(BaseModel):
    """Response for deleting a temporary upload."""

    success: bool
    file_id: str


class AgentMarketStateContext(BaseModel):
    """Optional market-state hints supplied by the frontend."""

    trend_bias: str = Field(default="unknown")
    structure_position: str = Field(default="unknown")
    volatility_regime: str = Field(default="unknown")
    momentum_state: str = Field(default="unknown")
    summary: Optional[str] = None


class AgentMarketContext(BaseModel):
    """Optional asset scope and market-state context supplied by the frontend."""

    scope_mode: str = Field(default="global")
    asset_id: Optional[str] = None
    symbol: Optional[str] = None
    asset_name: Optional[str] = None
    exchange: Optional[str] = None
    timeframe: Optional[str] = None
    source_screen: Optional[str] = None
    watchlist_symbols: List[str] = Field(default_factory=list)
    market_state: AgentMarketStateContext = Field(default_factory=AgentMarketStateContext)


class AgentBackpackExecutionContext(BaseModel):
    """Optional Backpack execution gate supplied by the frontend."""

    enabled: bool = Field(
        default=False,
        description="Whether live Backpack trade execution is enabled for this request",
    )
    exchange: str = Field(
        default="backpack",
        description="Execution exchange identifier. Reserved for Backpack v1.",
    )


class AgentDriftExecutionContext(BaseModel):
    """Optional Drift execution gate supplied by the frontend."""

    enabled: bool = Field(
        default=False,
        description="Whether live Drift trade execution is enabled for this request",
    )
    exchange: str = Field(
        default="drift",
        description="Execution exchange identifier. Reserved for Drift v1.",
    )


class DriftExecutionWalletResponse(BaseModel):
    """Resolved Drift execution-wallet status for one authenticated user."""

    mode: str = Field(default="same_wallet")
    auth_wallet_address: Optional[str] = None
    execution_wallet_address: Optional[str] = None
    verified: bool = False
    same_wallet_required: bool = True
    linked_wallet_supported: bool = False
    backend_held_signer_enabled: bool = False
    notes: List[str] = Field(default_factory=list)


class DriftExecutionPrepareRequest(BaseModel):
    """Prepare a same-wallet Drift execution intent for client-side signing."""

    sub_account_id: int = Field(default=0, description="Drift subaccount index")
    market_type: str = Field(default="perp", description="Drift market type. v1 defaults to perp.")
    market_index: Optional[int] = Field(default=None, description="Optional Drift market index")
    symbol: Optional[str] = Field(default=None, description="Optional market symbol such as SOL-PERP")
    side: str = Field(..., description="Order side such as long, short, buy, or sell")
    order_type: str = Field(..., description="Order type such as limit or market")
    base_asset_amount: str = Field(..., description="Base asset amount as a string to preserve precision")
    price: Optional[str] = Field(default=None, description="Optional price for limit-style orders")
    reduce_only: bool = Field(default=False, description="Optional reduce-only flag")
    post_only: bool = Field(default=False, description="Optional post-only flag")
    immediate_or_cancel: bool = Field(default=False, description="Optional IOC flag")
    client_order_id: Optional[int] = Field(default=None, description="Optional client order ID")


class DriftExecutionRecordResponse(BaseModel):
    """Prepared or submitted Drift execution record."""

    execution_id: str
    status: str
    mode: str
    user_id: str
    auth_wallet_address: str
    execution_wallet_address: str
    same_wallet_required: bool = True
    sub_account_id: int
    order_intent: Dict[str, Any] = Field(default_factory=dict)
    requires_client_signature: bool = True
    prepared_transaction: Dict[str, Any] = Field(default_factory=dict)
    prepared_at: str
    expires_at: str
    submitted_at: Optional[str] = None
    transaction_signature: Optional[str] = None
    last_error: Optional[str] = None


class DriftExecutionSubmitRequest(BaseModel):
    """Submit a signed same-wallet Drift transaction."""

    execution_id: str = Field(..., description="Prepared Drift execution request ID")
    signed_transaction: str = Field(..., description="Signed transaction bytes encoded as base64 or base58")
    transaction_encoding: str = Field(
        default="base64",
        description="Signed transaction encoding: base64 (default) or base58",
    )
    skip_preflight: bool = Field(default=False, description="Whether to skip preflight on submit")
    max_retries: Optional[int] = Field(default=None, description="Optional Solana send max_retries")


class DriftExecutionSubmitResponse(BaseModel):
    """Submission response for a signed same-wallet Drift transaction."""

    success: bool
    execution_id: str
    status: str
    transaction_signature: Optional[str] = None
    submitted_at: Optional[str] = None
    rpc_url: str
    detail: Optional[str] = None


class AgentChatRequest(BaseModel):
    """Request body for multimodal agent chat."""

    message: str = Field(..., description="User message for the agent")
    scope_id: Optional[str] = Field(None, description="Optional memory scope for the chat session")
    user_id: Optional[str] = Field(None, description="Optional user ID for Mem0 long-term memory")
    conversation_style: str = Field(
        default="normal",
        description="Response style: normal, learning, concise, explanatory, or formal",
    )
    trading_style: str = Field(
        default="balanced",
        description=(
            "Trading analysis style: balanced, price_action, trend_following, "
            "momentum_breakout, mean_reversion, smart_money, risk_first, or systematic"
        ),
    )
    market_context: Optional[AgentMarketContext] = Field(
        default=None,
        description="Optional frontend market scope and market-state context",
    )
    backpack_execution: Optional[AgentBackpackExecutionContext] = Field(
        default=None,
        description="Optional frontend gate controlling whether Backpack live execution is allowed",
    )
    drift_execution: Optional[AgentDriftExecutionContext] = Field(
        default=None,
        description="Optional frontend gate controlling whether Drift live execution is allowed",
    )
    attachment_ids: List[str] = Field(default_factory=list, description="Temporary uploaded file IDs")


class AgentChatResponse(BaseModel):
    """Response body for multimodal agent chat."""

    response: str
    scope_id: Optional[str] = None
    user_id: Optional[str] = None
    conversation_style: str = "normal"
    trading_style: str = "balanced"
    market_context: Optional[AgentMarketContext] = None
    backpack_execution: Optional[AgentBackpackExecutionContext] = None
    drift_execution: Optional[AgentDriftExecutionContext] = None
    attachment_ids: List[str] = Field(default_factory=list)
    intent: Optional[Dict[str, Any]] = None


class ExchangeConnectionCreateRequest(BaseModel):
    """Create a stored exchange connection for a user."""

    user_id: Optional[str] = Field(
        default=None,
        description="Optional user ID override. In production this should come from auth.",
    )
    exchange: str = Field(default="backpack", description="Exchange identifier such as backpack")
    label: Optional[str] = Field(default=None, description="Optional user-facing label")
    api_key: str = Field(..., description="Exchange API key or public verification key")
    api_secret: str = Field(..., description="Exchange API secret or signing private key")
    trading_enabled: bool = Field(
        default=False,
        description="Whether this stored connection may be used for live execution",
    )
    read_only: bool = Field(
        default=True,
        description="Whether this stored connection is restricted to read-only usage",
    )
    is_active: bool = Field(
        default=True,
        description="Whether this connection becomes the active connection for its exchange",
    )


class ExchangeConnectionUpdateRequest(BaseModel):
    """Update non-secret metadata for a stored exchange connection."""

    user_id: Optional[str] = Field(
        default=None,
        description="Optional user ID override. In production this should come from auth.",
    )
    label: Optional[str] = Field(default=None, description="Optional new label")
    trading_enabled: Optional[bool] = Field(default=None, description="Optional live trading toggle")
    read_only: Optional[bool] = Field(default=None, description="Optional read-only toggle")
    is_active: Optional[bool] = Field(default=None, description="Optional active-connection toggle")


class ExchangeConnectionResponse(BaseModel):
    """Public-safe exchange connection metadata."""

    id: str
    user_id: str
    exchange: str
    label: str
    last4: str
    fingerprint: str
    trading_enabled: bool
    read_only: bool
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_used_at: Optional[str] = None
    revoked_at: Optional[str] = None


class ExchangeConnectionListResponse(BaseModel):
    """List response for stored exchange connections."""

    user_id: str
    connections: List[ExchangeConnectionResponse] = Field(default_factory=list)
    total: int = 0


class ExchangeConnectionDeleteResponse(BaseModel):
    """Delete response for one exchange connection."""

    success: bool
    connection_id: str
    user_id: str
    exchange: str


class WalletAuthNonceRequest(BaseModel):
    """Request a mobile wallet sign-in challenge."""

    wallet_address: str = Field(..., description="Solana wallet address that will sign the challenge")


class WalletAuthNonceResponse(BaseModel):
    """Sign-in challenge to be signed by the wallet."""

    wallet_address: str
    nonce: str
    message: str
    issued_at: str
    expires_at: str


class WalletAuthVerifyRequest(BaseModel):
    """Verify a signed mobile wallet challenge."""

    wallet_address: str = Field(..., description="Solana wallet address that signed the challenge")
    nonce: str = Field(..., description="Challenge nonce returned by the backend")
    signature: str = Field(..., description="Signed message bytes encoded as base64 or base58")
    signature_encoding: str = Field(
        default="base64",
        description="Signature encoding: base64 (default) or base58",
    )
    message: Optional[str] = Field(
        default=None,
        description="Optional original challenge message for client-side roundtrip validation",
    )


class WalletAuthVerifyResponse(BaseModel):
    """JWT/token response after wallet challenge verification."""

    access_token: str
    token_type: str
    expires_at: str
    user_id: str
    wallet_address: str
    nonce: str
    message: str


class AuthMeResponse(BaseModel):
    """Authenticated wallet identity."""

    user_id: str
    wallet_address: str


class MemoryCreateRequest(BaseModel):
    """Create a user memory."""

    user_id: str = Field(..., description="User ID that owns the memory")
    text: str = Field(..., description="Long-term memory text to save")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional memory metadata")


class MemoryCreateResponse(BaseModel):
    """Response for creating a user memory."""

    success: bool
    user_id: str
    data: Dict[str, Any] = Field(default_factory=dict)


class MemoryListResponse(BaseModel):
    """Response for listing or searching user memories."""

    user_id: str
    memories: List[Dict[str, Any]] = Field(default_factory=list)
    total: int
    query: Optional[str] = None


class MemoryDeleteResponse(BaseModel):
    """Response for deleting memory records."""

    success: bool
    user_id: str
    memory_id: Optional[str] = None
    deleted_all: bool = False


class MemoryHealthResponse(BaseModel):
    """Mem0 connectivity status."""

    enabled: bool
    healthy: bool
    base_url: str
    detail: Optional[str] = None
