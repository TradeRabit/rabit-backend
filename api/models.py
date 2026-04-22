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


class AssetSearchResponse(BaseModel):
    """Response for GET /api/assets/search"""
    query: str = Field(..., description="Search query used to match assets")
    assets: List[AssetListItem]
    total: int = Field(..., description="Total number of matched assets")


class AssetCategoryItem(BaseModel):
    """One available asset category and its asset count."""

    name: str = Field(..., description="Normalized category name")
    asset_count: int = Field(..., description="Number of tracked assets in this category")


class AssetCategoryListResponse(BaseModel):
    """Response for GET /api/assets/categories"""

    categories: List[AssetCategoryItem]
    total: int = Field(..., description="Total number of available categories")


class AssetCategoryAssetsResponse(BaseModel):
    """Response for GET /api/assets/categories/{category}"""

    category: str = Field(..., description="Normalized category name")
    assets: List[AssetListItem]
    total: int = Field(..., description="Total number of assets in the category")


class SupportedTradingAssetsResponse(BaseModel):
    """Response for GET /api/assets/supported"""

    assets: List[str] = Field(default_factory=list, description="Configured tracked asset symbols")
    total: int = Field(..., description="Total number of configured tracked assets")


class RelatedAssetsResponse(BaseModel):
    """Response for GET /api/assets/{symbol}/related"""

    symbol: str = Field(..., description="Requested asset symbol")
    primary_category: Optional[str] = Field(default=None, description="Primary category used for fallback matching")
    assets: List[AssetListItem]
    total: int = Field(..., description="Total number of related assets returned")


class TrendingAssetItem(AssetListItem):
    """One ranked trending asset item."""

    rank: int = Field(..., description="Rank position in the trending list")
    score: float = Field(..., description="Composite lightweight ranking score")
    volume_24h: Optional[float] = Field(default=None, description="24h volume used in ranking")
    reasons: List[str] = Field(default_factory=list, description="Human-readable ranking hints")


class TrendingAssetsResponse(BaseModel):
    """Response for GET /api/assets/trending"""

    assets: List[TrendingAssetItem]
    total: int = Field(..., description="Total number of trending assets returned")
    ranking_method: str = Field(..., description="Short description of the lightweight ranking approach")


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
    notional_volume_24h: Optional[float] = None
    base_volume_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    
    # Market data (futures)
    market_cap: Optional[float] = None
    fdv: Optional[float] = None
    open_interest: Optional[float] = None
    funding_rate: Optional[float] = None
    oracle_price: Optional[float] = None
    premium: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    max_leverage: Optional[float] = None
    only_isolated: Optional[bool] = None
    market_pair: Optional[str] = None
    full_name: Optional[str] = None
    token_index: Optional[int] = None
    is_canonical: Optional[bool] = None
    source_exchange: Optional[str] = None
    
    # Static info
    description: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    links: AssetLinks
    
    # Metadata
    last_updated: str


class AssetSummaryResponse(BaseModel):
    """Response for GET /api/assets/{symbol}/summary"""

    symbol: str
    name: str
    price: float
    change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    notional_volume_24h: Optional[float] = None
    base_volume_24h: Optional[float] = None
    market_cap: Optional[float] = None
    fdv: Optional[float] = None
    open_interest: Optional[float] = None
    funding_rate: Optional[float] = None
    oracle_price: Optional[float] = None
    premium: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    max_leverage: Optional[float] = None
    only_isolated: Optional[bool] = None
    market_pair: Optional[str] = None
    full_name: Optional[str] = None
    token_index: Optional[int] = None
    is_canonical: Optional[bool] = None
    source_exchange: Optional[str] = None
    primary_category: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    links: AssetLinks
    related_assets: List[AssetListItem] = Field(default_factory=list)
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
    onchain_registered: bool = False
    onchain_model_id: Optional[str] = None
    onchain_model_registry_pda: Optional[str] = None
    onchain_is_active: Optional[bool] = None
    onchain_is_verified: Optional[bool] = None
    onchain_base_cost_per_token: Optional[int] = None
    onchain_custom_contract: Optional[str] = None
    onchain_sync_error: Optional[str] = None


class ModelsListResponse(BaseModel):
    """Response for GET /api/models"""
    models: List[ModelInfoResponse]
    total: int
    enabled: int
    disabled: int
    last_updated: Optional[str] = None
    onchain_available: Optional[bool] = None
    onchain_registered_models: Optional[int] = None
    onchain_active_models: Optional[int] = None
    onchain_verified_models: Optional[int] = None
    onchain_last_updated: Optional[str] = None
    onchain_error: Optional[str] = None


class ModelStatsResponse(BaseModel):
    """Model statistics"""
    total_models: int
    enabled_models: int
    disabled_models: int
    models_with_tools: int
    models_with_reasoning: int
    providers: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Statistics grouped by provider")
    last_updated: Optional[str] = None
    onchain_available: Optional[bool] = None
    onchain_registered_models: Optional[int] = None
    onchain_active_models: Optional[int] = None
    onchain_verified_models: Optional[int] = None
    onchain_last_updated: Optional[str] = None
    onchain_error: Optional[str] = None


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


class AgentNewsContext(BaseModel):
    """Optional news-headline hints supplied by the frontend."""

    tail_titles: List[str] = Field(default_factory=list)


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
    news_context: AgentNewsContext = Field(default_factory=AgentNewsContext)


class AssetNewsItem(BaseModel):
    """One news item for a tracked asset."""

    title: str
    url: str
    snippet: Optional[str] = None
    date: Optional[str] = None
    source: Optional[str] = None
    symbol: str
    detected_at: Optional[str] = None
    freshness_seconds: Optional[int] = None
    is_new: Optional[bool] = None


class AssetNewsResponse(BaseModel):
    """Response for GET /api/news/assets/{symbol}."""

    timestamp: str
    symbol: str
    news: List[AssetNewsItem] = Field(default_factory=list)
    total: int


class AgentExecutionGateContext(BaseModel):
    """Generic execution gate supplied by the frontend."""

    enabled: bool = Field(
        default=False,
        description="Whether live execution is enabled for this request",
    )
    exchange: str = Field(
        default="phantom",
        description="Execution venue identifier. The backend normalizes this into the Phantom-first runtime.",
    )


class AgentToolPreferences(BaseModel):
    """Frontend toggles controlling assist tool behavior for one request."""

    web_search_enabled: bool = Field(
        default=True,
        description="Whether web/news research tools are allowed for this request",
    )
    memory_enabled: bool = Field(
        default=True,
        description="Whether Mem0-backed long-term memory is allowed for this request",
    )
    plan_enabled: bool = Field(
        default=True,
        description="Whether structured planning behavior is enabled for this request",
    )
    auto_execute_enabled: bool = Field(
        default=False,
        description="Whether live exchange execution can be attempted for this request",
    )


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
    execution_gate: Optional[AgentExecutionGateContext] = Field(
        default=None,
        description="Optional Phantom-first live execution gate for this request.",
    )
    tool_preferences: Optional[AgentToolPreferences] = Field(
        default=None,
        description="Optional frontend tool toggles such as web search, memory, planning, and auto execution",
    )
    attachment_ids: List[str] = Field(default_factory=list, description="Temporary uploaded file IDs")


class OpenRouterSessionCostPhaseResponse(BaseModel):
    """One aggregated OpenRouter usage phase inside a chat/session scope."""

    phase: str
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class OpenRouterSessionCostResponse(BaseModel):
    """Accumulated OpenRouter usage and estimated cost for one scope_id session."""

    scope_id: str
    user_id: Optional[str] = None
    currency: str = "USD"
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    model_ids: List[str] = Field(default_factory=list)
    phases: List[OpenRouterSessionCostPhaseResponse] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MonitoringCostSummaryResponse(BaseModel):
    """Accumulated monitoring cost for one scope_id session."""

    scope_id: str
    user_id: Optional[str] = None
    currency: str = "USD"
    alert_setup_cost_usd: float = 0.0
    trigger_cost_usd: float = 0.0
    monitoring_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    alert_setup_count: int = 0
    trigger_count: int = 0
    active_alert_count: int = 0
    active_symbol_count: int = 0
    active_symbols: List[str] = Field(default_factory=list)
    total_symbol_hours: float = 0.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class OnchainAiUsagePreviewResponse(BaseModel):
    """Contract-aligned AI usage settlement preview derived from backend USD summaries."""

    scope_id: str
    user_id: Optional[str] = None
    cluster: str
    program_id: str
    config_pda: str
    fee_recipient_pda: str
    backend_authority_wallet: Optional[str] = None
    owner_wallet_address: Optional[str] = None
    spending_profile_pda: Optional[str] = None
    delegated_signer_pda: Optional[str] = None
    payment_mint: Optional[str] = None
    payment_token_symbol: str = "USDC"
    payment_mint_decimals: int = 6
    payment_token_usd_price: float = 1.0
    usage_type: str = "text"
    tokens_used: int = 0
    model_ids: List[str] = Field(default_factory=list)
    model_id: Optional[str] = None
    model_registry_pda: Optional[str] = None
    model_cost_usd: float = 0.0
    service_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    base_cost_units: int = 0
    service_cost_units: int = 0
    chargeable_cost_units: int = 0
    markup_bps: int = 0
    markup_amount_units: int = 0
    platform_fee_bps: int = 0
    platform_fee_amount_units: int = 0
    total_charged_units: int = 0
    instruction_buildable: bool = False
    instruction_name: Optional[str] = None
    preview_mode: str = "aggregate_scope_preview"
    notes: List[str] = Field(default_factory=list)


class ServiceCostSummaryResponse(BaseModel):
    """Combined backend service cost for one scope_id session."""

    scope_id: str
    user_id: Optional[str] = None
    currency: str = "USD"
    model_cost_usd: float = 0.0
    monitor_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    session_cost: Optional[OpenRouterSessionCostResponse] = None
    monitoring_cost: Optional[MonitoringCostSummaryResponse] = None
    onchain_ai_usage: Optional[OnchainAiUsagePreviewResponse] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ContractReadinessResponse(BaseModel):
    """Current on-chain setup and balance readiness for one wallet-authenticated user."""

    user_id: Optional[str] = None
    wallet_address: str
    cluster: str
    program_id: str
    backend_authority_wallet: Optional[str] = None
    backend_signer_ready: bool = False
    backend_signer_pubkey: Optional[str] = None
    payment_mint: str
    payment_token_symbol: str = "USDC"
    payment_mint_decimals: int = 6
    payment_token_usd_price: float = 1.0
    minimum_balance_usd: float = 1.0
    user_token_account: str
    fee_recipient_token_account: str
    user_token_account_exists: bool = False
    fee_recipient_token_account_exists: bool = False
    payment_balance_amount: int = 0
    payment_balance_ui_amount: float = 0.0
    payment_balance_usd: float = 0.0
    balance_ok: bool = False
    spending_profile_pda: Optional[str] = None
    spending_profile_exists: bool = False
    spending_profile_usage_sequence: Optional[int] = None
    spending_profile_payment_mint: Optional[str] = None
    delegated_signer_pda: Optional[str] = None
    delegated_signer_exists: bool = False
    delegated_signer_active: bool = False
    delegated_signer_expired: bool = False
    delegated_signer_expires_at: Optional[int] = None
    delegated_signer_spending_limit: Optional[int] = None
    setup_complete: bool = False
    can_chat: bool = False
    notes: List[str] = Field(default_factory=list)


class ContractSetupTransactionResponse(BaseModel):
    """Unsigned setup transaction for one contract onboarding action."""

    action: str
    classification: str
    cluster: str
    program_id: str
    authority: str
    transaction_encoding: str = "base64"
    recent_blockhash: str
    last_valid_block_height: Optional[int] = None
    message_version: str = "v0"
    unsigned_transaction: str
    unsigned_message: str
    signing_instructions: List[str] = Field(default_factory=list)


class ContractSignedTransactionSubmitRequest(BaseModel):
    """Submit a wallet-signed Rabit contract setup transaction."""

    action: str
    signed_transaction: str
    transaction_encoding: str = Field(default="base64")
    skip_preflight: bool = False
    max_retries: Optional[int] = None


class ContractTransactionSubmitResponse(BaseModel):
    """Submission response for one setup or backend-signed contract transaction."""

    success: bool
    action: str
    transaction_signature: str
    rpc_url: str
    detail: Optional[str] = None


class ContractAiUsageSettleRequest(BaseModel):
    """Request to settle one scope's accumulated AI usage on-chain."""

    scope_id: str = Field(..., description="Scope/session ID whose accumulated usage should be settled")


class ContractAiUsageSettlementResponse(BaseModel):
    """Result of settling one scope's AI usage through the Rabit contract."""

    success: bool
    scope_id: str
    user_id: Optional[str] = None
    wallet_address: str
    transaction_signature: str
    rpc_url: str
    settlement_record: Dict[str, Any] = Field(default_factory=dict)
    onchain_ai_usage: Optional[OnchainAiUsagePreviewResponse] = None
    detail: Optional[str] = None


class ContractAccountResponse(BaseModel):
    """One decoded on-chain contract account plus its PDA metadata."""

    cluster: str
    program_id: str
    account_type: str
    pda: str
    exists: bool
    data: Optional[Dict[str, Any]] = None


class ContractModelRegistryListResponse(BaseModel):
    """List of decoded on-chain model registry accounts."""

    cluster: str
    program_id: str
    models: List[Dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class ContractAiUsageRecordResponse(BaseModel):
    """One decoded on-chain AI usage record."""

    cluster: str
    program_id: str
    wallet_address: str
    spending_profile_pda: str
    usage_record_pda: str
    usage_sequence: Optional[int] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class ContractAiUsageRecordListResponse(BaseModel):
    """List of decoded on-chain AI usage records for one wallet."""

    cluster: str
    program_id: str
    wallet_address: str
    spending_profile_pda: str
    records: List[ContractAiUsageRecordResponse] = Field(default_factory=list)
    total: int = 0


class ContractSettlementRecordResponse(BaseModel):
    """One locally persisted settlement record for on-chain AI usage."""

    scope_id: str
    user_id: Optional[str] = None
    wallet_address: Optional[str] = None
    transaction_signature: Optional[str] = None
    rpc_url: Optional[str] = None
    submitted_at: Optional[str] = None
    usage_sequence: Optional[int] = None
    model_id: Optional[str] = None
    base_cost_units: Optional[int] = None
    service_cost_units: Optional[int] = None
    total_charged_units: Optional[int] = None
    onchain_record_found: Optional[bool] = None
    onchain_record_pda: Optional[str] = None
    onchain_record: Optional[Dict[str, Any]] = None


class ContractSettlementListResponse(BaseModel):
    """List of locally persisted settlement records."""

    settlements: List[ContractSettlementRecordResponse] = Field(default_factory=list)
    total: int = 0


class ContractBackendInstructionResponse(BaseModel):
    """Backend-signed Rabit contract transaction response."""

    success: bool
    action: str
    cluster: str
    program_id: str
    instruction_name: str
    signer: str
    transaction_signature: str
    rpc_url: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    detail: Optional[str] = None


class ContractAdminUpdatePlatformFeeRequest(BaseModel):
    """Update platform fee bps through the contract authority."""

    platform_fee_bps: int = Field(..., ge=0)


class ContractAdminUpdateDefaultMarkupRequest(BaseModel):
    """Update default markup bps through the contract authority."""

    default_markup_bps: int = Field(..., ge=0)


class ContractAdminUpdateAuthorityRequest(BaseModel):
    """Update the contract authority wallet."""

    new_authority: str


class ContractAdminUpdateBackendAuthorityRequest(BaseModel):
    """Update the backend authority wallet stored in config."""

    new_backend_authority: str


class ContractClaimFeesRequest(BaseModel):
    """Claim lamports from the fee recipient PDA into the authority wallet."""

    amount: int = Field(..., gt=0)


class ContractModelRegisterRequest(BaseModel):
    """Register one backend model in the on-chain model registry."""

    model_id: str
    provider: str
    base_cost_per_token: int = Field(..., ge=0)
    features: str = ""


class ContractModelUpdateRequest(BaseModel):
    """Update one on-chain model registry entry."""

    model_id: str
    base_cost_per_token: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    features: Optional[str] = None
    custom_contract: Optional[str] = None


class ContractModelDeactivateRequest(BaseModel):
    """Deactivate one on-chain model registry entry."""

    model_id: str


class ContractDirectAiUsagePrepareRequest(BaseModel):
    """Prepare a user-signed direct AI usage transaction for one backend scope."""

    scope_id: str = Field(..., description="Scope/session ID whose accumulated usage should be settled directly by the user")


class AgentPipelineArtifactResponse(BaseModel):
    """One persisted pipeline artifact for a chat/session scope."""

    artifact_id: str
    scope_id: str
    user_id: Optional[str] = None
    node_name: str
    kind: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    expires_at: str


class AgentPipelineArtifactListResponse(BaseModel):
    """Persisted pipeline artifacts for one scope_id."""

    scope_id: str
    user_id: Optional[str] = None
    artifacts: List[AgentPipelineArtifactResponse] = Field(default_factory=list)
    total: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AgentChatResponse(BaseModel):
    """Response body for multimodal agent chat."""

    response: str
    scope_id: Optional[str] = None
    user_id: Optional[str] = None
    conversation_style: str = "normal"
    trading_style: str = "balanced"
    market_context: Optional[AgentMarketContext] = None
    execution_gate: Optional[AgentExecutionGateContext] = None
    tool_preferences: Optional[AgentToolPreferences] = None
    attachment_ids: List[str] = Field(default_factory=list)
    intent: Optional[Dict[str, Any]] = None
    agent_pipeline: Optional[Dict[str, Any]] = None
    session_cost: Optional[OpenRouterSessionCostResponse] = None
    service_cost: Optional[ServiceCostSummaryResponse] = None


class AgentSessionMessageResponse(BaseModel):
    """One persisted message inside an agent session."""

    role: str
    content: str
    timestamp: str


class AgentSessionSummaryResponse(BaseModel):
    """One persisted agent session summary for sidebar/history views."""

    scope_id: str
    title: str
    message_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_message: Optional[str] = None
    user_id: Optional[str] = None
    scope_mode: Optional[str] = None
    symbol: Optional[str] = None
    exchange: Optional[str] = None
    source_screen: Optional[str] = None


class AgentSessionListResponse(BaseModel):
    """List of persisted agent sessions for one user."""

    sessions: List[AgentSessionSummaryResponse] = Field(default_factory=list)
    total: int = 0


class AgentSessionDetailResponse(AgentSessionSummaryResponse):
    """Detailed persisted agent session with full message history."""

    messages: List[AgentSessionMessageResponse] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentSessionUpdateRequest(BaseModel):
    """Rename metadata for one persisted agent session."""

    title: str = Field(..., description="New non-empty session title")


class AgentSessionDeleteResponse(BaseModel):
    """Delete response for one persisted agent session."""

    success: bool
    scope_id: str


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
    username: Optional[str] = None


class UsernameUpdateRequest(BaseModel):
    """Update the caller's username."""

    username: str = Field(..., description="New username for the authenticated user")


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
