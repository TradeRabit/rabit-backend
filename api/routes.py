"""
API Routes
REST API endpoints untuk Rabit Mobile
"""
from fastapi import APIRouter, File, Header, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import Optional, List
import logging
import asyncio
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone

from agents.core import TradingAgent
from agents.ai_usage_settlement import build_onchain_ai_usage_preview
from agents.contract_execution import (
    AiUsageAlreadySettledError,
    ContractExecutionError,
    build_unsigned_instruction_payload,
    ensure_backend_matches_contract_authority,
    get_ai_usage_settlement_database,
    get_contract_readiness,
    submit_backend_signed_instruction,
    submit_signed_transaction,
)
from agents.auth import (
    JWTAuthError,
    WalletAuthError,
    create_wallet_auth_nonce,
    verify_access_token,
    verify_wallet_auth,
)
from agents.pipeline.conversation_style import normalize_conversation_style
from agents.auth.base58 import b58decode
from agents.pipeline.execution_gate import merge_legacy_execution_gates, normalize_execution_gate
from agents.pipeline.market_context import normalize_market_context
from agents.pipeline.tool_preferences import normalize_tool_preferences
from agents.memory import Mem0DisabledError, Mem0RequestError, get_conversation_database, get_mem0_client
from agents.openrouter import get_openrouter_session_cost_service
from agents.pipeline.artifacts import get_pipeline_artifact_service
from agents.service_costs import get_monitoring_cost_service
from agents.user_profiles import UsernameValidationError, get_user_profile_service
from agents.pipeline.trading_style import normalize_trading_style
from agents.tools_registry import register_trading_tools
from agents.uploads import UploadValidationError, get_upload_manager
from contract import derive_ai_usage_pda, derive_model_registry_pda, get_rabit_contract_sdk, load_deployment
from config.settings import settings
from ws.services import get_market_service
from ws.handlers import MarketDataHandler
from ws.news import get_news_monitor
from ws.phantom import HyperliquidHistoryDownloader
from ws.utils.categories import get_category_stats, get_primary_category, normalize_category
from api.models import (
    AssetCategoryAssetsResponse,
    AssetCategoryListResponse,
    AssetListResponse,
    AssetListItem,
    AssetNewsItem,
    AssetNewsResponse,
    AssetDetailResponse,
    AssetSummaryResponse,
    RelatedAssetsResponse,
    AssetSearchResponse,
    OHLCResponse,
    ErrorResponse,
    ModelsListResponse,
    ModelInfoResponse,
    ModelStatsResponse,
    ModelToggleRequest,
    AgentUploadResponse,
    AgentUploadDeleteResponse,
    AgentChatRequest,
    AgentChatResponse,
    AgentSessionDetailResponse,
    AgentSessionDeleteResponse,
    AgentSessionListResponse,
    AgentSessionMessageResponse,
    AgentSessionSummaryResponse,
    AgentSessionUpdateRequest,
    AgentPipelineArtifactListResponse,
    AgentPipelineArtifactResponse,
    AuthMeResponse,
    ContractAccountResponse,
    ContractAdminUpdateAuthorityRequest,
    ContractAdminUpdateBackendAuthorityRequest,
    ContractAdminUpdateDefaultMarkupRequest,
    ContractAdminUpdatePlatformFeeRequest,
    ContractAiUsageSettleRequest,
    ContractAiUsageSettlementResponse,
    ContractAiUsageRecordListResponse,
    ContractAiUsageRecordResponse,
    ContractBackendInstructionResponse,
    ContractClaimFeesRequest,
    ContractDirectAiUsagePrepareRequest,
    ContractModelDeactivateRequest,
    ContractModelRegisterRequest,
    ContractModelRegistryListResponse,
    ContractModelUpdateRequest,
    ContractReadinessResponse,
    ContractSetupTransactionResponse,
    ContractSignedTransactionSubmitRequest,
    ContractSettlementListResponse,
    ContractSettlementRecordResponse,
    ContractTransactionSubmitResponse,
    UsernameUpdateRequest,
    MemoryCreateRequest,
    MemoryCreateResponse,
    MemoryDeleteResponse,
    MemoryHealthResponse,
    MemoryListResponse,
    MonitoringCostSummaryResponse,
    OpenRouterSessionCostResponse,
    ServiceCostSummaryResponse,
    SupportedTradingAssetsResponse,
    TrendingAssetItem,
    TrendingAssetsResponse,
    WalletAuthNonceRequest,
    WalletAuthNonceResponse,
    WalletAuthVerifyRequest,
    WalletAuthVerifyResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")
_agent_tools_registered = False


def get_agent(scope_id: Optional[str] = None, user_id: Optional[str] = None) -> TradingAgent:
    """Create a trading agent with tools registered once."""
    global _agent_tools_registered
    if not _agent_tools_registered:
        register_trading_tools()
        _agent_tools_registered = True
    return TradingAgent(scope_id=scope_id, user_id=user_id)


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO datetime string into an aware UTC datetime when possible."""
    if not value:
        return None
    try:
        normalized = str(value).strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _enrich_news_item_timing(item: dict, fallback_detected_at: str) -> dict:
    """Attach consistent freshness helpers to one news item."""
    detected_at = item.get("detected_at") or fallback_detected_at
    detected_dt = _parse_iso_datetime(detected_at)
    now_dt = datetime.now(timezone.utc)

    freshness_seconds: Optional[int] = None
    if detected_dt is not None:
        freshness_seconds = max(0, int((now_dt - detected_dt).total_seconds()))

    is_new = (
        freshness_seconds is not None
        and freshness_seconds <= settings.NEWS_IS_NEW_WINDOW_SECONDS
    )

    return {
        **item,
        "detected_at": detected_at,
        "freshness_seconds": freshness_seconds,
        "is_new": is_new,
    }


def _raise_mem0_http_error(exc: Exception) -> None:
    """Translate Mem0 client errors into HTTP responses."""
    if isinstance(exc, Mem0DisabledError):
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if isinstance(exc, Mem0RequestError):
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    raise HTTPException(status_code=500, detail=str(exc)) from exc


def _raise_user_profile_http_error(exc: Exception) -> None:
    """Translate user profile errors into HTTP responses."""
    if isinstance(exc, UsernameValidationError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise HTTPException(status_code=500, detail=str(exc)) from exc


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """Extract bearer token from Authorization header."""
    if not authorization:
        return None
    prefix = "bearer "
    if authorization.lower().startswith(prefix):
        return authorization[len(prefix):].strip()
    return None


def _get_authenticated_user(authorization: Optional[str]) -> Optional[dict]:
    """Return verified auth claims from Authorization header, if present."""
    token = _extract_bearer_token(authorization)
    if not token:
        return None
    try:
        return verify_access_token(token)
    except JWTAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _resolve_request_user_id(
    *,
    provided_user_id: Optional[str],
    auth_user: Optional[dict],
) -> Optional[str]:
    """Prefer authenticated user identity and reject mismatches."""
    if auth_user is None:
        return provided_user_id

    auth_user_id = auth_user.get("user_id")
    if provided_user_id and provided_user_id != auth_user_id:
        raise HTTPException(
            status_code=403,
            detail="Provided user_id does not match the authenticated wallet user.",
        )
    return auth_user_id


def _require_resolved_user_id(user_id: Optional[str]) -> str:
    """Require a resolved user identity for protected resource ownership."""
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user or explicit user_id is required for this endpoint.",
        )
    return user_id


def _format_sse(event_name: str, payload: dict) -> str:
    """Format an SSE event payload."""
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _serialize_agent_intent(agent) -> Optional[dict]:
    """Safely serialize the agent's last routed intent for API responses."""
    intent = getattr(agent, "last_intent", None)
    if intent is None:
        return None
    if hasattr(intent, "model_dump"):
        return intent.model_dump()
    if isinstance(intent, dict):
        return intent
    return None


def _serialize_agent_pipeline(agent) -> Optional[dict]:
    """Safely serialize the agent's last pipeline trace for API responses."""
    pipeline = getattr(agent, "last_pipeline_trace", None)
    if pipeline is None:
        return None
    if hasattr(pipeline, "model_dump"):
        return pipeline.model_dump()
    if isinstance(pipeline, dict):
        return pipeline
    return None


def _serialize_conversation_style(style: Optional[str]) -> str:
    """Normalize style values before returning them to clients."""
    return normalize_conversation_style(style)


def _serialize_trading_style(style: Optional[str]) -> str:
    """Normalize trading style values before returning them to clients."""
    return normalize_trading_style(style)


def _serialize_market_context(context: Optional[dict]) -> dict:
    """Normalize market context values before returning them to clients."""
    return normalize_market_context(context)


def _serialize_execution_gate(config: Optional[dict]) -> dict:
    """Normalize generic execution-gate values before returning them to clients."""
    return normalize_execution_gate(config)


def _serialize_tool_preferences(config: Optional[dict]) -> dict:
    """Normalize tool-preference values before returning them to clients."""
    return normalize_tool_preferences(config)


async def _get_onchain_model_registry_snapshot(*, force_refresh: bool = False):
    """Load one cached on-chain model registry snapshot for model API enrichment."""
    from agents.openrouter import get_contract_model_registry_service

    service = get_contract_model_registry_service()
    return await service.get_snapshot(force_refresh=force_refresh)


def _serialize_model_info_response(model, onchain_snapshot) -> ModelInfoResponse:
    """Serialize one backend model with on-chain registry enrichment."""
    from agents.openrouter import get_contract_model_registry_service

    payload = model.model_dump()
    payload.update(
        get_contract_model_registry_service().enrich_model(model.id, onchain_snapshot)
    )
    return ModelInfoResponse(**payload)


def _serialize_session_cost(summary: Optional[dict]) -> Optional[dict]:
    """Return session-cost payloads unchanged when present."""
    return summary or None


def _serialize_monitoring_cost(summary: Optional[dict]) -> Optional[dict]:
    """Return monitoring-cost payloads unchanged when present."""
    return summary or None


def _build_agent_session_metadata(
    *,
    request: AgentChatRequest,
    user_id: Optional[str],
) -> dict:
    """Build metadata for one persisted assist session."""
    market_context = normalize_market_context(
        request.market_context.model_dump() if request.market_context else None
    )
    symbol = market_context.get("symbol")
    source_screen = market_context.get("source_screen")
    scope_mode = market_context.get("scope_mode")
    exchange = market_context.get("exchange")
    asset_name = market_context.get("asset_name")
    tool_preferences = normalize_tool_preferences(
        request.tool_preferences.model_dump() if request.tool_preferences else None
    )

    title = None
    message_text = str(request.message or "").strip()
    if message_text:
        title = message_text[:50] + ("..." if len(message_text) > 50 else "")
    elif symbol:
        title = f"{symbol} Assist"
    elif asset_name:
        title = f"{asset_name} Assist"

    metadata = {
        "user_id": user_id,
        "title": title,
        "scope_mode": scope_mode,
        "symbol": symbol,
        "exchange": exchange,
        "asset_name": asset_name,
        "source_screen": source_screen,
        "tool_preferences": tool_preferences,
        "conversation_style": normalize_conversation_style(request.conversation_style),
        "trading_style": normalize_trading_style(request.trading_style),
    }
    return {key: value for key, value in metadata.items() if value not in (None, "")}


def _persist_agent_session_metadata(
    *,
    scope_id: Optional[str],
    request: AgentChatRequest,
    user_id: Optional[str],
) -> None:
    """Persist frontend session metadata after one agent turn completes."""
    normalized_scope_id = str(scope_id or "").strip()
    if not normalized_scope_id:
        return

    metadata = _build_agent_session_metadata(request=request, user_id=user_id)
    if not metadata:
        return

    get_conversation_database().update_session_metadata(normalized_scope_id, metadata)


def _serialize_agent_session_summary(raw: dict) -> AgentSessionSummaryResponse:
    """Convert raw conversation-db session summaries into API responses."""
    return AgentSessionSummaryResponse(
        scope_id=raw.get("scope_id", ""),
        title=raw.get("title") or "Untitled",
        message_count=raw.get("message_count", 0),
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
        last_message=raw.get("last_message"),
        user_id=raw.get("user_id"),
        scope_mode=raw.get("scope_mode"),
        symbol=raw.get("symbol"),
        exchange=raw.get("exchange"),
        source_screen=raw.get("source_screen"),
    )


def _build_service_cost_summary(
    *,
    scope_id: Optional[str],
    user_id: Optional[str] = None,
    session_cost: Optional[dict] = None,
    monitoring_cost: Optional[dict] = None,
) -> Optional[dict]:
    """Build a combined service-cost payload for one scope."""
    normalized_scope_id = str(scope_id or "").strip()
    if not normalized_scope_id:
        return None

    model_summary = session_cost
    if model_summary is None:
        model_summary = get_openrouter_session_cost_service().get_scope_summary(scope_id=normalized_scope_id)

    monitor_summary = monitoring_cost
    if monitor_summary is None:
        monitor_summary = get_monitoring_cost_service().get_scope_summary(scope_id=normalized_scope_id)

    if not model_summary and not monitor_summary:
        return None

    created_at_candidates = [
        value
        for value in [
            (model_summary or {}).get("created_at"),
            (monitor_summary or {}).get("created_at"),
        ]
        if value
    ]
    updated_at_candidates = [
        value
        for value in [
            (model_summary or {}).get("updated_at"),
            (monitor_summary or {}).get("updated_at"),
        ]
        if value
    ]

    onchain_ai_usage = build_onchain_ai_usage_preview(
        scope_id=normalized_scope_id,
        user_id=(model_summary or {}).get("user_id") or (monitor_summary or {}).get("user_id") or user_id,
        session_cost=model_summary,
        monitoring_cost=monitor_summary,
    )

    return {
        "scope_id": normalized_scope_id,
        "user_id": (model_summary or {}).get("user_id") or (monitor_summary or {}).get("user_id") or user_id,
        "currency": (model_summary or {}).get("currency") or (monitor_summary or {}).get("currency") or "USD",
        "model_cost_usd": round(float((model_summary or {}).get("estimated_cost_usd") or 0.0), 10),
        "monitor_cost_usd": round(float((monitor_summary or {}).get("total_cost_usd") or 0.0), 10),
        "total_cost_usd": round(
            float((model_summary or {}).get("estimated_cost_usd") or 0.0)
            + float((monitor_summary or {}).get("total_cost_usd") or 0.0),
            10,
        ),
        "session_cost": model_summary,
        "monitoring_cost": monitor_summary,
        "onchain_ai_usage": onchain_ai_usage,
        "created_at": min(created_at_candidates) if created_at_candidates else None,
        "updated_at": max(updated_at_candidates) if updated_at_candidates else None,
    }


def _require_wallet_authenticated_user(auth_user: Optional[dict]) -> tuple[str, str]:
    """Require wallet-authenticated identity and return user_id plus wallet address."""
    if auth_user is None:
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    user_id = auth_user.get("user_id")
    wallet_address = auth_user.get("wallet_address")
    if not user_id or not wallet_address:
        raise HTTPException(
            status_code=401,
            detail="Wallet-authenticated user is required for contract-protected endpoints.",
        )
    return user_id, wallet_address


def _raise_contract_execution_http_error(exc: Exception) -> None:
    """Translate contract execution/setup errors into HTTP responses."""
    if isinstance(exc, AiUsageAlreadySettledError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if isinstance(exc, ContractExecutionError):
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise HTTPException(status_code=500, detail=str(exc)) from exc


async def _require_contract_chat_ready(auth_user: Optional[dict]) -> Optional[dict]:
    """Enforce on-chain payment readiness before allowing paid assist messages."""
    if not settings.RABIT_AI_USAGE_ENFORCE_CHAT_BALANCE:
        return None
    if auth_user is None:
        return None

    user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    readiness = await get_contract_readiness(wallet_address=wallet_address, user_id=user_id)
    if not readiness.get("setup_complete"):
        raise HTTPException(
            status_code=403,
            detail={
                "message": "On-chain AI usage setup is incomplete.",
                "readiness": readiness,
            },
        )
    if not readiness.get("balance_ok"):
        raise HTTPException(
            status_code=402,
            detail={
                "message": f"Insufficient payment balance. Minimum required is ${settings.RABIT_AI_USAGE_CHAT_MIN_BALANCE_USD:.2f}.",
                "readiness": readiness,
            },
        )
    return readiness


def _normalize_exchange_filter(exchange: Optional[str]) -> Optional[str]:
    """Normalize frontend market source filters into Phantom spot/futures channels."""
    if exchange is None:
        return None

    normalized_exchange = str(exchange).strip().lower()
    if not normalized_exchange:
        return None

    if normalized_exchange not in {"phantom", "spot", "futures"}:
        raise HTTPException(
            status_code=400,
            detail="exchange must be one of 'phantom', 'spot', or 'futures'.",
        )

    if normalized_exchange == "spot":
        return "phantom_spot"
    return "phantom_futures"


def _decode_signed_transaction(payload: str, encoding: str) -> bytes:
    """Decode a signed transaction using base64 or base58 input."""
    normalized = str(encoding or "base64").strip().lower()
    if normalized == "base64":
        import base64

        try:
            return base64.b64decode(payload)
        except Exception as exc:
            raise ValueError("Invalid base64 signed_transaction payload.") from exc
    if normalized == "base58":
        try:
            return b58decode(payload)
        except Exception as exc:
            raise ValueError("Invalid base58 signed_transaction payload.") from exc
    raise ValueError("transaction_encoding must be 'base64' or 'base58'.")


def _serialize_contract_value(value):
    """Normalize dataclass-backed contract SDK values into JSON-safe dicts."""
    if value is None:
        return None
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "__dict__"):
        return {
            key: serialized
            for key, serialized in vars(value).items()
            if not key.startswith("_")
        }
    return value


async def _build_unsigned_contract_action_payload(
    *,
    payer: str,
    instruction,
    action: str,
    rpc_url: str,
) -> ContractSetupTransactionResponse:
    payload = await build_unsigned_instruction_payload(
        payer=payer,
        instruction=instruction,
        classification="contract_setup_mobile_signing_payload",
        action=action,
        rpc_url=rpc_url,
    )
    return ContractSetupTransactionResponse(**payload)


def _build_backend_contract_response(
    *,
    action: str,
    instruction_name: str,
    submitted: dict,
    metadata: Optional[dict] = None,
    detail: Optional[str] = None,
) -> ContractBackendInstructionResponse:
    deployment = load_deployment(settings.RABIT_CONTRACT_CLUSTER)
    return ContractBackendInstructionResponse(
        success=True,
        action=action,
        cluster=deployment.cluster,
        program_id=deployment.program_id,
        instruction_name=instruction_name,
        signer=str(submitted.get("signer") or ""),
        transaction_signature=str(submitted["transaction_signature"]),
        rpc_url=str(submitted["rpc_url"]),
        metadata=metadata or {},
        detail=detail,
    )


def _require_contract_authority_signer() -> str:
    """Ensure the configured backend signer matches the deployed contract authority."""
    try:
        return ensure_backend_matches_contract_authority()
    except Exception as exc:
        _raise_contract_execution_http_error(exc)
        raise


def _build_scope_onchain_preview(*, scope_id: str, user_id: str) -> dict:
    """Load one service-cost summary and require a buildable on-chain AI usage preview."""
    summary = _build_service_cost_summary(scope_id=scope_id, user_id=user_id)
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"No service cost summary found for scope_id '{scope_id}'.",
        )
    owner_user_id = summary.get("user_id")
    if owner_user_id and owner_user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Requested scope_id does not belong to the authenticated user.",
        )
    preview = summary.get("onchain_ai_usage")
    if not preview or not preview.get("instruction_buildable"):
        raise HTTPException(
            status_code=409,
            detail="This scope is not ready for on-chain settlement yet. Ensure it resolves to one model and payment mint configuration is complete.",
        )
    return preview


# ============================================================================
# Wallet Auth Endpoints
# ============================================================================

@router.post(
    "/auth/wallet/nonce",
    response_model=WalletAuthNonceResponse,
    tags=["Auth"],
    summary="Create wallet sign-in challenge",
)
async def create_wallet_nonce(request: WalletAuthNonceRequest):
    """Create a one-time wallet sign-in challenge for mobile clients."""
    try:
        payload = create_wallet_auth_nonce(wallet_address=request.wallet_address)
        return WalletAuthNonceResponse(**payload)
    except Exception as exc:
        logger.error(f"Error creating wallet auth nonce: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/auth/wallet/verify",
    response_model=WalletAuthVerifyResponse,
    tags=["Auth"],
    summary="Verify wallet signature and issue JWT",
)
async def verify_wallet_signin(request: WalletAuthVerifyRequest):
    """Verify a signed wallet challenge and issue a bearer token."""
    try:
        payload = verify_wallet_auth(
            wallet_address=request.wallet_address,
            nonce=request.nonce,
            signature=request.signature,
            signature_encoding=request.signature_encoding,
            message=request.message,
        )
        return WalletAuthVerifyResponse(**payload)
    except WalletAuthError as exc:
        logger.error(f"Wallet auth verification failed: {exc}")
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected wallet auth verification error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/auth/me",
    response_model=AuthMeResponse,
    tags=["Auth"],
    summary="Return authenticated wallet identity",
)
async def get_authenticated_me(authorization: Optional[str] = Header(default=None)):
    """Return the current authenticated wallet identity."""
    auth_user = _get_authenticated_user(authorization)
    if auth_user is None:
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    profile = get_user_profile_service().get_profile(
        user_id=auth_user["user_id"],
        wallet_address=auth_user["wallet_address"],
    )
    return AuthMeResponse(
        user_id=auth_user["user_id"],
        wallet_address=auth_user["wallet_address"],
        username=profile.get("username"),
    )


@router.patch(
    "/auth/me/username",
    response_model=AuthMeResponse,
    tags=["Auth"],
    summary="Update authenticated username",
)
async def update_authenticated_username(
    request: UsernameUpdateRequest,
    authorization: Optional[str] = Header(default=None),
):
    """Create or update the authenticated user's username."""
    auth_user = _get_authenticated_user(authorization)
    if auth_user is None:
        raise HTTPException(status_code=401, detail="Missing bearer token.")

    try:
        profile = get_user_profile_service().set_username(
            user_id=auth_user["user_id"],
            wallet_address=auth_user["wallet_address"],
            username=request.username,
        )
        return AuthMeResponse(
            user_id=auth_user["user_id"],
            wallet_address=auth_user["wallet_address"],
            username=profile.get("username"),
        )
    except Exception as exc:
        logger.error(f"Error updating authenticated username: {exc}")
        _raise_user_profile_http_error(exc)


@router.get(
    "/openrouter/session-costs/{scope_id}",
    response_model=OpenRouterSessionCostResponse,
    tags=["Service Cost"],
    summary="Return accumulated OpenRouter session cost for one scope",
)
async def get_openrouter_session_cost(
    scope_id: str,
    user_id: Optional[str] = Query(
        None,
        description="Optional explicit user ID when no bearer token is available",
    ),
    authorization: Optional[str] = Header(default=None),
):
    """Return one scope_id's accumulated OpenRouter usage and estimated cost."""
    auth_user = _get_authenticated_user(authorization)
    resolved_user_id = _resolve_request_user_id(
        provided_user_id=user_id,
        auth_user=auth_user,
    )
    if not resolved_user_id:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user or explicit user_id is required for session cost access.",
        )

    summary = get_openrouter_session_cost_service().get_scope_summary(scope_id=scope_id)
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"No OpenRouter session cost summary found for scope_id '{scope_id}'.",
        )

    owner_user_id = summary.get("user_id")
    if owner_user_id and owner_user_id != resolved_user_id:
        raise HTTPException(
            status_code=403,
            detail="Requested scope_id does not belong to the authenticated user.",
        )

    return OpenRouterSessionCostResponse(**summary)


@router.get(
    "/service-costs/{scope_id}",
    response_model=ServiceCostSummaryResponse,
    tags=["Service Cost"],
    summary="Return combined model and monitoring service cost for one scope",
)
async def get_service_cost(
    scope_id: str,
    user_id: Optional[str] = Query(
        None,
        description="Optional explicit user ID when no bearer token is available",
    ),
    authorization: Optional[str] = Header(default=None),
):
    """Return one scope_id's combined model and monitoring cost summary."""
    auth_user = _get_authenticated_user(authorization)
    resolved_user_id = _resolve_request_user_id(
        provided_user_id=user_id,
        auth_user=auth_user,
    )
    if not resolved_user_id:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user or explicit user_id is required for service cost access.",
        )

    summary = _build_service_cost_summary(scope_id=scope_id, user_id=resolved_user_id)
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"No service cost summary found for scope_id '{scope_id}'.",
        )

    owner_user_id = summary.get("user_id")
    if owner_user_id and owner_user_id != resolved_user_id:
        raise HTTPException(
            status_code=403,
            detail="Requested scope_id does not belong to the authenticated user.",
        )

    return ServiceCostSummaryResponse(**summary)


@router.get(
    "/contract/readiness",
    response_model=ContractReadinessResponse,
    tags=["Contract"],
    summary="Return on-chain setup and balance readiness for the authenticated wallet",
)
async def get_contract_setup_readiness(authorization: Optional[str] = Header(default=None)):
    """Return current Rabit contract onboarding and balance readiness."""
    auth_user = _get_authenticated_user(authorization)
    user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        readiness = await get_contract_readiness(wallet_address=wallet_address, user_id=user_id)
        return ContractReadinessResponse(**readiness)
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.get(
    "/contract/config",
    response_model=ContractAccountResponse,
    tags=["Contract"],
    summary="Return the decoded Rabit platform config account",
)
async def get_contract_config_account():
    """Return decoded PlatformConfig state from the deployed Rabit contract."""
    try:
        sdk = get_rabit_contract_sdk()
        deployment = load_deployment(settings.RABIT_CONTRACT_CLUSTER)
        account = await sdk.get_config()
        return ContractAccountResponse(
            cluster=deployment.cluster,
            program_id=deployment.program_id,
            account_type="platform_config",
            pda=deployment.config_pda,
            exists=account is not None,
            data=_serialize_contract_value(account),
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.get(
    "/contract/spending-profile",
    response_model=ContractAccountResponse,
    tags=["Contract"],
    summary="Return the authenticated wallet's decoded spending profile",
)
async def get_contract_spending_profile(authorization: Optional[str] = Header(default=None)):
    """Return decoded SpendingProfile for the authenticated wallet."""
    auth_user = _get_authenticated_user(authorization)
    _user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        sdk = get_rabit_contract_sdk()
        deployment = load_deployment(settings.RABIT_CONTRACT_CLUSTER)
        readiness = await get_contract_readiness(wallet_address=wallet_address)
        account = await sdk.get_spending_profile(wallet_address)
        return ContractAccountResponse(
            cluster=deployment.cluster,
            program_id=deployment.program_id,
            account_type="spending_profile",
            pda=str(readiness.get("spending_profile_pda") or ""),
            exists=account is not None,
            data=_serialize_contract_value(account),
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.get(
    "/contract/delegated-signer",
    response_model=ContractAccountResponse,
    tags=["Contract"],
    summary="Return the authenticated wallet's backend delegated signer account",
)
async def get_contract_delegated_signer_account(authorization: Optional[str] = Header(default=None)):
    """Return decoded DelegatedSigner account for the authenticated wallet and backend authority."""
    auth_user = _get_authenticated_user(authorization)
    _user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        deployment = load_deployment(settings.RABIT_CONTRACT_CLUSTER)
        if not deployment.backend_authority_wallet:
            raise ContractExecutionError("Contract deployment metadata has no backend authority wallet.")
        sdk = get_rabit_contract_sdk()
        readiness = await get_contract_readiness(wallet_address=wallet_address)
        account = await sdk.get_delegated_signer(wallet_address, deployment.backend_authority_wallet)
        return ContractAccountResponse(
            cluster=deployment.cluster,
            program_id=deployment.program_id,
            account_type="delegated_signer",
            pda=str(readiness.get("delegated_signer_pda") or ""),
            exists=account is not None,
            data=_serialize_contract_value(account),
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.get(
    "/contract/model-registry",
    response_model=ContractModelRegistryListResponse,
    tags=["Contract"],
    summary="Return decoded on-chain model registry entries",
)
async def list_contract_model_registry_accounts():
    """Return every decodable on-chain ModelRegistry account."""
    try:
        sdk = get_rabit_contract_sdk()
        deployment = load_deployment(settings.RABIT_CONTRACT_CLUSTER)
        accounts = await sdk.list_model_registry_accounts()
        models = [
            {
                "pda": pda,
                **(_serialize_contract_value(account) or {}),
            }
            for pda, account in accounts
        ]
        return ContractModelRegistryListResponse(
            cluster=deployment.cluster,
            program_id=deployment.program_id,
            models=models,
            total=len(models),
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.get(
    "/contract/model-registry/{model_id:path}",
    response_model=ContractAccountResponse,
    tags=["Contract"],
    summary="Return one decoded on-chain model registry entry",
)
async def get_contract_model_registry_account(model_id: str):
    """Return decoded ModelRegistry entry for one model ID."""
    try:
        sdk = get_rabit_contract_sdk()
        deployment = load_deployment(settings.RABIT_CONTRACT_CLUSTER)
        account = await sdk.get_model_registry(model_id)
        model_registry_pda = derive_model_registry_pda(
            model_id,
            cluster=deployment.cluster,
            program_id=deployment.program_id,
        )[0]
        return ContractAccountResponse(
            cluster=deployment.cluster,
            program_id=deployment.program_id,
            account_type="model_registry",
            pda=model_registry_pda,
            exists=account is not None,
            data=_serialize_contract_value(account),
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.get(
    "/contract/ai-usage",
    response_model=ContractAiUsageRecordListResponse,
    tags=["Contract"],
    summary="Return decoded on-chain AI usage records for the authenticated wallet",
)
async def list_contract_ai_usage_records(authorization: Optional[str] = Header(default=None)):
    """Return every decodable AiUsageRecord for the authenticated wallet's spending profile."""
    auth_user = _get_authenticated_user(authorization)
    _user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        sdk = get_rabit_contract_sdk()
        deployment = load_deployment(settings.RABIT_CONTRACT_CLUSTER)
        readiness = await get_contract_readiness(wallet_address=wallet_address)
        spending_profile_pda = readiness.get("spending_profile_pda")
        if not spending_profile_pda:
            raise HTTPException(status_code=404, detail="Spending profile was not found on-chain.")
        records = await sdk.list_ai_usage_records(spending_profile=spending_profile_pda)
        payload = [
            ContractAiUsageRecordResponse(
                cluster=deployment.cluster,
                program_id=deployment.program_id,
                wallet_address=wallet_address,
                spending_profile_pda=spending_profile_pda,
                usage_record_pda=pda,
                usage_sequence=None,
                data=_serialize_contract_value(record) or {},
            )
            for pda, record in records
        ]
        return ContractAiUsageRecordListResponse(
            cluster=deployment.cluster,
            program_id=deployment.program_id,
            wallet_address=wallet_address,
            spending_profile_pda=spending_profile_pda,
            records=payload,
            total=len(payload),
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.get(
    "/contract/ai-usage/{usage_sequence}",
    response_model=ContractAiUsageRecordResponse,
    tags=["Contract"],
    summary="Return one decoded on-chain AI usage record for the authenticated wallet",
)
async def get_contract_ai_usage_record(usage_sequence: int, authorization: Optional[str] = Header(default=None)):
    """Return one AiUsageRecord by usage sequence for the authenticated wallet."""
    auth_user = _get_authenticated_user(authorization)
    _user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        sdk = get_rabit_contract_sdk()
        deployment = load_deployment(settings.RABIT_CONTRACT_CLUSTER)
        readiness = await get_contract_readiness(wallet_address=wallet_address)
        spending_profile_pda = readiness.get("spending_profile_pda")
        if not spending_profile_pda:
            raise HTTPException(status_code=404, detail="Spending profile was not found on-chain.")
        record = await sdk.get_ai_usage_record(spending_profile_pda, usage_sequence)
        if record is None:
            raise HTTPException(status_code=404, detail="AI usage record was not found on-chain.")
        usage_record_pda = derive_ai_usage_pda(
            spending_profile_pda,
            usage_sequence,
            cluster=deployment.cluster,
            program_id=deployment.program_id,
        )[0]
        return ContractAiUsageRecordResponse(
            cluster=deployment.cluster,
            program_id=deployment.program_id,
            wallet_address=wallet_address,
            spending_profile_pda=spending_profile_pda,
            usage_record_pda=usage_record_pda,
            usage_sequence=usage_sequence,
            data=_serialize_contract_value(record) or {},
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/setup/spending-profile/prepare",
    response_model=ContractSetupTransactionResponse,
    tags=["Contract"],
    summary="Prepare unsigned transaction to initialize a spending profile",
)
async def prepare_contract_spending_profile(authorization: Optional[str] = Header(default=None)):
    """Build an unsigned initialize_spending_profile transaction for the authenticated wallet."""
    auth_user = _get_authenticated_user(authorization)
    _user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        readiness = await get_contract_readiness(wallet_address=wallet_address)
        if readiness.get("spending_profile_exists"):
            raise HTTPException(status_code=409, detail="Spending profile is already initialized.")

        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_initialize_spending_profile_instruction(
            owner=wallet_address,
            payment_mint=settings.RABIT_AI_USAGE_PAYMENT_MINT,
        )
        return await _build_unsigned_contract_action_payload(
            payer=wallet_address,
            instruction=instruction,
            action="initialize_spending_profile",
            rpc_url=sdk.rpc_url,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/setup/delegated-signer/prepare",
    response_model=ContractSetupTransactionResponse,
    tags=["Contract"],
    summary="Prepare unsigned transaction to create the backend delegated signer",
)
async def prepare_contract_delegated_signer(authorization: Optional[str] = Header(default=None)):
    """Build an unsigned create_delegated_signer transaction for the authenticated wallet."""
    auth_user = _get_authenticated_user(authorization)
    _user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        readiness = await get_contract_readiness(wallet_address=wallet_address)
        if readiness.get("delegated_signer_exists"):
            raise HTTPException(status_code=409, detail="Delegated signer is already initialized.")
        if not readiness.get("backend_authority_wallet"):
            raise ContractExecutionError("Contract deployment metadata has no backend authority wallet.")

        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_create_delegated_signer_instruction(
            owner=wallet_address,
            delegate=readiness["backend_authority_wallet"],
            expiry_duration=settings.RABIT_AI_USAGE_DELEGATION_EXPIRY_SECONDS,
            spending_limit=settings.RABIT_AI_USAGE_DELEGATION_SPENDING_LIMIT_UNITS,
        )
        return await _build_unsigned_contract_action_payload(
            payer=wallet_address,
            instruction=instruction,
            action="create_delegated_signer",
            rpc_url=sdk.rpc_url,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/setup/approve-delegate/prepare",
    response_model=ContractSetupTransactionResponse,
    tags=["Contract"],
    summary="Prepare unsigned transaction to approve the backend delegated signer on the payment token account",
)
async def prepare_contract_approve_delegate(authorization: Optional[str] = Header(default=None)):
    """Build an unsigned approve_spending_delegate transaction for the authenticated wallet."""
    auth_user = _get_authenticated_user(authorization)
    _user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        readiness = await get_contract_readiness(wallet_address=wallet_address)
        if not readiness.get("spending_profile_exists"):
            raise HTTPException(status_code=409, detail="Spending profile must be initialized before delegate approval.")
        if not readiness.get("delegated_signer_exists"):
            raise HTTPException(status_code=409, detail="Delegated signer must be created before delegate approval.")
        if not readiness.get("user_token_account_exists"):
            raise HTTPException(status_code=409, detail="User payment token account does not exist yet.")

        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_approve_spending_delegate_instruction(
            owner=wallet_address,
            delegate=readiness["backend_authority_wallet"],
            user_token_account=readiness["user_token_account"],
        )
        return await _build_unsigned_contract_action_payload(
            payer=wallet_address,
            instruction=instruction,
            action="approve_spending_delegate",
            rpc_url=sdk.rpc_url,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/setup/revoke-delegate/prepare",
    response_model=ContractSetupTransactionResponse,
    tags=["Contract"],
    summary="Prepare unsigned transaction to revoke the payment-token delegate",
)
async def prepare_contract_revoke_delegate(authorization: Optional[str] = Header(default=None)):
    """Build an unsigned revoke_spending_delegate transaction for the authenticated wallet."""
    auth_user = _get_authenticated_user(authorization)
    _user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        readiness = await get_contract_readiness(wallet_address=wallet_address)
        if not readiness.get("spending_profile_exists"):
            raise HTTPException(status_code=409, detail="Spending profile is not initialized.")
        if not readiness.get("user_token_account_exists"):
            raise HTTPException(status_code=409, detail="User payment token account does not exist yet.")
        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_revoke_spending_delegate_instruction(
            owner=wallet_address,
            user_token_account=readiness["user_token_account"],
        )
        return await _build_unsigned_contract_action_payload(
            payer=wallet_address,
            instruction=instruction,
            action="revoke_spending_delegate",
            rpc_url=sdk.rpc_url,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/setup/close-spending-profile/prepare",
    response_model=ContractSetupTransactionResponse,
    tags=["Contract"],
    summary="Prepare unsigned transaction to close the spending profile",
)
async def prepare_contract_close_spending_profile(authorization: Optional[str] = Header(default=None)):
    """Build an unsigned close_spending_profile transaction for the authenticated wallet."""
    auth_user = _get_authenticated_user(authorization)
    _user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        readiness = await get_contract_readiness(wallet_address=wallet_address)
        if not readiness.get("spending_profile_exists"):
            raise HTTPException(status_code=409, detail="Spending profile is not initialized.")
        if not readiness.get("user_token_account_exists"):
            raise HTTPException(status_code=409, detail="User payment token account does not exist yet.")
        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_close_spending_profile_instruction(
            owner=wallet_address,
            user_token_account=readiness["user_token_account"],
        )
        return await _build_unsigned_contract_action_payload(
            payer=wallet_address,
            instruction=instruction,
            action="close_spending_profile",
            rpc_url=sdk.rpc_url,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/setup/revoke-delegated-signer/prepare",
    response_model=ContractSetupTransactionResponse,
    tags=["Contract"],
    summary="Prepare unsigned transaction to revoke the backend delegated signer account",
)
async def prepare_contract_revoke_delegated_signer(authorization: Optional[str] = Header(default=None)):
    """Build an unsigned revoke_delegated_signer transaction for the authenticated wallet."""
    auth_user = _get_authenticated_user(authorization)
    _user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        readiness = await get_contract_readiness(wallet_address=wallet_address)
        if not readiness.get("delegated_signer_exists"):
            raise HTTPException(status_code=409, detail="Delegated signer is not initialized.")
        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_revoke_delegated_signer_instruction(
            owner=wallet_address,
            delegate=readiness["backend_authority_wallet"],
        )
        return await _build_unsigned_contract_action_payload(
            payer=wallet_address,
            instruction=instruction,
            action="revoke_delegated_signer",
            rpc_url=sdk.rpc_url,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/setup/close-delegated-signer/prepare",
    response_model=ContractSetupTransactionResponse,
    tags=["Contract"],
    summary="Prepare unsigned transaction to close the backend delegated signer account",
)
async def prepare_contract_close_delegated_signer(authorization: Optional[str] = Header(default=None)):
    """Build an unsigned close_delegated_signer transaction for the authenticated wallet."""
    auth_user = _get_authenticated_user(authorization)
    _user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        readiness = await get_contract_readiness(wallet_address=wallet_address)
        if not readiness.get("delegated_signer_exists"):
            raise HTTPException(status_code=409, detail="Delegated signer is not initialized.")
        if readiness.get("delegated_signer_active"):
            raise HTTPException(status_code=409, detail="Delegated signer must be revoked before it can be closed.")
        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_close_delegated_signer_instruction(
            owner=wallet_address,
            delegate=readiness["backend_authority_wallet"],
        )
        return await _build_unsigned_contract_action_payload(
            payer=wallet_address,
            instruction=instruction,
            action="close_delegated_signer",
            rpc_url=sdk.rpc_url,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/setup/submit",
    response_model=ContractTransactionSubmitResponse,
    tags=["Contract"],
    summary="Submit a signed Rabit contract setup transaction",
)
async def submit_contract_setup_transaction(
    request: ContractSignedTransactionSubmitRequest,
    authorization: Optional[str] = Header(default=None),
):
    """Submit a user-signed Rabit contract setup transaction to Solana RPC."""
    auth_user = _get_authenticated_user(authorization)
    _user_id, _wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        raw_tx = _decode_signed_transaction(request.signed_transaction, request.transaction_encoding)
        tx_signature = await submit_signed_transaction(
            signed_transaction=raw_tx,
            rpc_url=get_rabit_contract_sdk().rpc_url,
            skip_preflight=request.skip_preflight,
            max_retries=request.max_retries,
        )
        return ContractTransactionSubmitResponse(
            success=True,
            action=request.action,
            transaction_signature=tx_signature,
            rpc_url=get_rabit_contract_sdk().rpc_url,
            detail="Signed contract setup transaction submitted to Solana RPC.",
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/ai-usage/direct/prepare",
    response_model=ContractSetupTransactionResponse,
    tags=["Contract"],
    summary="Prepare unsigned transaction to record one scope's AI usage directly from the user's token account",
)
async def prepare_contract_direct_ai_usage(
    request: ContractDirectAiUsagePrepareRequest,
    authorization: Optional[str] = Header(default=None),
):
    """Build an unsigned record_ai_usage transaction for one scope so the user can sign directly."""
    auth_user = _get_authenticated_user(authorization)
    user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        readiness = await get_contract_readiness(wallet_address=wallet_address, user_id=user_id)
        if not readiness.get("spending_profile_exists"):
            raise HTTPException(status_code=409, detail="Spending profile was not found on-chain.")
        if not readiness.get("user_token_account_exists"):
            raise HTTPException(status_code=409, detail="User payment token account does not exist yet.")
        if not readiness.get("fee_recipient_token_account_exists"):
            raise HTTPException(status_code=409, detail="Fee recipient token account does not exist yet.")

        preview = _build_scope_onchain_preview(scope_id=request.scope_id, user_id=user_id)
        sdk = get_rabit_contract_sdk()
        spending_profile = await sdk.get_spending_profile(wallet_address)
        if spending_profile is None:
            raise HTTPException(status_code=409, detail="Spending profile was not found on-chain.")

        instruction = sdk.build_record_ai_usage_instruction(
            user=wallet_address,
            owner=wallet_address,
            user_token_account=readiness["user_token_account"],
            fee_recipient_token_account=readiness["fee_recipient_token_account"],
            payment_mint=settings.RABIT_AI_USAGE_PAYMENT_MINT,
            model_id=preview["model_id"],
            base_cost=int(preview["base_cost_units"]),
            service_cost=int(preview["service_cost_units"]),
            usage_type=preview["usage_type"],
            tokens_used=int(preview["tokens_used"]),
            usage_sequence=int(spending_profile.usage_sequence),
            markup_bps=int(preview["markup_bps"]),
        )
        return await _build_unsigned_contract_action_payload(
            payer=wallet_address,
            instruction=instruction,
            action="record_ai_usage",
            rpc_url=sdk.rpc_url,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/ai-usage/settle",
    response_model=ContractAiUsageSettlementResponse,
    tags=["Contract"],
    summary="Settle one scope's accumulated AI usage on-chain using the delegated backend signer",
)
async def settle_contract_ai_usage(
    request: ContractAiUsageSettleRequest,
    authorization: Optional[str] = Header(default=None),
):
    """Submit a backend-signed record_ai_usage_with_delegation transaction for one scope."""
    auth_user = _get_authenticated_user(authorization)
    user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        readiness = await get_contract_readiness(wallet_address=wallet_address, user_id=user_id)
        if not readiness.get("setup_complete"):
            raise HTTPException(status_code=403, detail="Contract setup is incomplete for this wallet.")
        if not readiness.get("backend_signer_ready"):
            raise ContractExecutionError("Backend contract signer is not configured or could not be loaded.")
        if not readiness.get("balance_ok"):
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient payment balance. Minimum required is ${settings.RABIT_AI_USAGE_CHAT_MIN_BALANCE_USD:.2f}.",
            )

        settlement_db = get_ai_usage_settlement_database()
        existing = settlement_db.get(request.scope_id)
        if existing and existing.get("transaction_signature"):
            raise AiUsageAlreadySettledError(
                f"Scope '{request.scope_id}' has already been settled on-chain."
            )

        preview = _build_scope_onchain_preview(scope_id=request.scope_id, user_id=user_id)

        sdk = get_rabit_contract_sdk()
        spending_profile = await sdk.get_spending_profile(wallet_address)
        if spending_profile is None:
            raise HTTPException(status_code=409, detail="Spending profile was not found on-chain.")

        instruction = sdk.build_record_ai_usage_with_delegation_instruction(
            owner=wallet_address,
            delegate=readiness["backend_authority_wallet"],
            user_token_account=readiness["user_token_account"],
            fee_recipient_token_account=readiness["fee_recipient_token_account"],
            payment_mint=settings.RABIT_AI_USAGE_PAYMENT_MINT,
            model_id=preview["model_id"],
            base_cost=int(preview["base_cost_units"]),
            service_cost=int(preview["service_cost_units"]),
            usage_type=preview["usage_type"],
            tokens_used=int(preview["tokens_used"]),
            usage_sequence=int(spending_profile.usage_sequence),
            markup_bps=int(preview["markup_bps"]),
        )
        submitted = await submit_backend_signed_instruction(
            instruction=instruction,
            payer=readiness["backend_signer_pubkey"] or readiness["backend_authority_wallet"],
            rpc_url=sdk.rpc_url,
        )

        settlement_record = {
            "scope_id": request.scope_id,
            "user_id": user_id,
            "wallet_address": wallet_address,
            "transaction_signature": submitted["transaction_signature"],
            "rpc_url": submitted["rpc_url"],
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "usage_sequence": int(spending_profile.usage_sequence),
            "model_id": preview["model_id"],
            "base_cost_units": int(preview["base_cost_units"]),
            "service_cost_units": int(preview["service_cost_units"]),
            "total_charged_units": int(preview["total_charged_units"]),
        }
        settlement_db.upsert(request.scope_id, settlement_record)

        return ContractAiUsageSettlementResponse(
            success=True,
            scope_id=request.scope_id,
            user_id=user_id,
            wallet_address=wallet_address,
            transaction_signature=submitted["transaction_signature"],
            rpc_url=submitted["rpc_url"],
            settlement_record=settlement_record,
            onchain_ai_usage=preview,
            detail="AI usage settlement submitted to Solana RPC.",
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.get(
    "/contract/settlements",
    response_model=ContractSettlementListResponse,
    tags=["Contract"],
    summary="Return locally persisted AI usage settlement records for the authenticated wallet",
)
async def list_contract_settlements(authorization: Optional[str] = Header(default=None)):
    """Return local settlement history filtered to the authenticated wallet."""
    auth_user = _get_authenticated_user(authorization)
    user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        settlement_db = get_ai_usage_settlement_database()
        records = settlement_db.list(user_id=user_id, wallet_address=wallet_address)
        return ContractSettlementListResponse(
            settlements=[ContractSettlementRecordResponse(**record) for record in records],
            total=len(records),
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.get(
    "/contract/settlements/{scope_id}",
    response_model=ContractSettlementRecordResponse,
    tags=["Contract"],
    summary="Return one locally persisted AI usage settlement record with optional on-chain reconciliation",
)
async def get_contract_settlement(scope_id: str, authorization: Optional[str] = Header(default=None)):
    """Return one settlement record and, when possible, its matching on-chain AiUsageRecord."""
    auth_user = _get_authenticated_user(authorization)
    user_id, wallet_address = _require_wallet_authenticated_user(auth_user)
    try:
        settlement_db = get_ai_usage_settlement_database()
        record = settlement_db.get(scope_id)
        if not record:
            raise HTTPException(status_code=404, detail="Settlement record was not found.")
        if record.get("user_id") and record.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Requested settlement does not belong to the authenticated user.")

        readiness = await get_contract_readiness(wallet_address=wallet_address, user_id=user_id)
        spending_profile_pda = readiness.get("spending_profile_pda")
        onchain_record = None
        onchain_record_pda = None
        if spending_profile_pda and record.get("usage_sequence") is not None:
            sdk = get_rabit_contract_sdk()
            onchain_record = await sdk.get_ai_usage_record(spending_profile_pda, int(record["usage_sequence"]))
            if onchain_record is not None:
                deployment = load_deployment(settings.RABIT_CONTRACT_CLUSTER)
                onchain_record_pda = derive_ai_usage_pda(
                    spending_profile_pda,
                    int(record["usage_sequence"]),
                    cluster=deployment.cluster,
                    program_id=deployment.program_id,
                )[0]

        return ContractSettlementRecordResponse(
            **record,
            onchain_record_found=onchain_record is not None,
            onchain_record_pda=onchain_record_pda,
            onchain_record=_serialize_contract_value(onchain_record),
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/model-registry/register",
    response_model=ContractBackendInstructionResponse,
    tags=["Contract"],
    summary="Register one backend model in the on-chain model registry",
)
async def register_contract_model(request: ContractModelRegisterRequest):
    """Submit a backend-signed register_model instruction."""
    try:
        authority = _require_contract_authority_signer()
        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_register_model_instruction(
            authority=authority,
            model_id=request.model_id,
            provider=request.provider,
            base_cost_per_token=request.base_cost_per_token,
            features=request.features,
        )
        submitted = await submit_backend_signed_instruction(
            instruction=instruction,
            payer=authority,
            rpc_url=sdk.rpc_url,
        )
        return _build_backend_contract_response(
            action="register_model",
            instruction_name="register_model",
            submitted=submitted,
            metadata={"model_id": request.model_id, "provider": request.provider},
            detail="On-chain model registry entry registered successfully.",
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/model-registry/update",
    response_model=ContractBackendInstructionResponse,
    tags=["Contract"],
    summary="Update one on-chain model registry entry",
)
async def update_contract_model(request: ContractModelUpdateRequest):
    """Submit a backend-signed update_model instruction."""
    try:
        authority = _require_contract_authority_signer()
        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_update_model_instruction(
            authority=authority,
            model_id=request.model_id,
            base_cost_per_token=request.base_cost_per_token,
            is_active=request.is_active,
            features=request.features,
            custom_contract=request.custom_contract,
        )
        submitted = await submit_backend_signed_instruction(
            instruction=instruction,
            payer=authority,
            rpc_url=sdk.rpc_url,
        )
        return _build_backend_contract_response(
            action="update_model",
            instruction_name="update_model",
            submitted=submitted,
            metadata={"model_id": request.model_id},
            detail="On-chain model registry entry updated successfully.",
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/model-registry/deactivate",
    response_model=ContractBackendInstructionResponse,
    tags=["Contract"],
    summary="Deactivate one on-chain model registry entry",
)
async def deactivate_contract_model(request: ContractModelDeactivateRequest):
    """Submit a backend-signed deactivate_model instruction."""
    try:
        authority = _require_contract_authority_signer()
        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_deactivate_model_instruction(
            authority=authority,
            model_id=request.model_id,
        )
        submitted = await submit_backend_signed_instruction(
            instruction=instruction,
            payer=authority,
            rpc_url=sdk.rpc_url,
        )
        return _build_backend_contract_response(
            action="deactivate_model",
            instruction_name="deactivate_model",
            submitted=submitted,
            metadata={"model_id": request.model_id},
            detail="On-chain model registry entry deactivated successfully.",
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/admin/update-platform-fee",
    response_model=ContractBackendInstructionResponse,
    tags=["Contract"],
    summary="Update the Rabit contract platform fee basis points",
)
async def update_contract_platform_fee(request: ContractAdminUpdatePlatformFeeRequest):
    """Submit a backend-signed update_platform_fee instruction."""
    try:
        authority = _require_contract_authority_signer()
        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_update_platform_fee_instruction(
            authority=authority,
            new_platform_fee_bps=request.platform_fee_bps,
        )
        submitted = await submit_backend_signed_instruction(instruction=instruction, payer=authority, rpc_url=sdk.rpc_url)
        return _build_backend_contract_response(
            action="update_platform_fee",
            instruction_name="update_platform_fee",
            submitted=submitted,
            metadata={"platform_fee_bps": request.platform_fee_bps},
            detail="Contract platform fee updated successfully.",
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/admin/update-default-markup",
    response_model=ContractBackendInstructionResponse,
    tags=["Contract"],
    summary="Update the Rabit contract default markup basis points",
)
async def update_contract_default_markup(request: ContractAdminUpdateDefaultMarkupRequest):
    """Submit a backend-signed update_default_markup instruction."""
    try:
        authority = _require_contract_authority_signer()
        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_update_default_markup_instruction(
            authority=authority,
            new_default_markup_bps=request.default_markup_bps,
        )
        submitted = await submit_backend_signed_instruction(instruction=instruction, payer=authority, rpc_url=sdk.rpc_url)
        return _build_backend_contract_response(
            action="update_default_markup",
            instruction_name="update_default_markup",
            submitted=submitted,
            metadata={"default_markup_bps": request.default_markup_bps},
            detail="Contract default markup updated successfully.",
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/admin/update-authority",
    response_model=ContractBackendInstructionResponse,
    tags=["Contract"],
    summary="Update the Rabit contract authority wallet",
)
async def update_contract_authority(request: ContractAdminUpdateAuthorityRequest):
    """Submit a backend-signed update_authority instruction."""
    try:
        authority = _require_contract_authority_signer()
        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_update_authority_instruction(
            authority=authority,
            new_authority=request.new_authority,
        )
        submitted = await submit_backend_signed_instruction(instruction=instruction, payer=authority, rpc_url=sdk.rpc_url)
        return _build_backend_contract_response(
            action="update_authority",
            instruction_name="update_authority",
            submitted=submitted,
            metadata={"new_authority": request.new_authority},
            detail="Contract authority updated successfully.",
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/admin/update-backend-authority",
    response_model=ContractBackendInstructionResponse,
    tags=["Contract"],
    summary="Update the Rabit contract backend authority wallet",
)
async def update_contract_backend_authority(request: ContractAdminUpdateBackendAuthorityRequest):
    """Submit a backend-signed update_backend_authority instruction."""
    try:
        authority = _require_contract_authority_signer()
        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_update_backend_authority_instruction(
            authority=authority,
            new_backend_authority=request.new_backend_authority,
        )
        submitted = await submit_backend_signed_instruction(instruction=instruction, payer=authority, rpc_url=sdk.rpc_url)
        return _build_backend_contract_response(
            action="update_backend_authority",
            instruction_name="update_backend_authority",
            submitted=submitted,
            metadata={"new_backend_authority": request.new_backend_authority},
            detail="Contract backend authority updated successfully.",
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/admin/toggle-pause",
    response_model=ContractBackendInstructionResponse,
    tags=["Contract"],
    summary="Toggle the Rabit contract paused state",
)
async def toggle_contract_pause():
    """Submit a backend-signed toggle_pause instruction."""
    try:
        authority = _require_contract_authority_signer()
        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_toggle_pause_instruction(authority=authority)
        submitted = await submit_backend_signed_instruction(instruction=instruction, payer=authority, rpc_url=sdk.rpc_url)
        return _build_backend_contract_response(
            action="toggle_pause",
            instruction_name="toggle_pause",
            submitted=submitted,
            metadata={},
            detail="Contract pause state toggled successfully.",
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.post(
    "/contract/admin/claim-fees",
    response_model=ContractBackendInstructionResponse,
    tags=["Contract"],
    summary="Claim lamports from the fee recipient PDA into the authority wallet",
)
async def claim_contract_fees(request: ContractClaimFeesRequest):
    """Submit a backend-signed claim_fees instruction."""
    try:
        authority = _require_contract_authority_signer()
        sdk = get_rabit_contract_sdk()
        instruction = sdk.build_claim_fees_instruction(authority=authority, amount=request.amount)
        submitted = await submit_backend_signed_instruction(instruction=instruction, payer=authority, rpc_url=sdk.rpc_url)
        return _build_backend_contract_response(
            action="claim_fees",
            instruction_name="claim_fees",
            submitted=submitted,
            metadata={"amount": request.amount},
            detail="Contract fee recipient lamports claimed successfully.",
        )
    except Exception as exc:
        _raise_contract_execution_http_error(exc)


@router.get(
    "/agent/artifacts/{scope_id}",
    response_model=AgentPipelineArtifactListResponse,
    tags=["Agent"],
    summary="Return persisted pipeline artifacts for one scope",
)
async def get_agent_pipeline_artifacts(
    scope_id: str,
    user_id: Optional[str] = Query(
        None,
        description="Optional explicit user ID when no bearer token is available",
    ),
    authorization: Optional[str] = Header(default=None),
):
    """Return persisted pipeline artifacts for one chat/session scope."""
    auth_user = _get_authenticated_user(authorization)
    resolved_user_id = _resolve_request_user_id(
        provided_user_id=user_id,
        auth_user=auth_user,
    )
    if not resolved_user_id:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user or explicit user_id is required for pipeline artifact access.",
        )

    summary = get_pipeline_artifact_service().list_scope_artifacts(scope_id=scope_id)
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"No pipeline artifacts found for scope_id '{scope_id}'.",
        )

    owner_user_id = summary.get("user_id")
    if owner_user_id and owner_user_id != resolved_user_id:
        raise HTTPException(
            status_code=403,
            detail="Requested scope_id does not belong to the authenticated user.",
        )

    artifacts = [
        AgentPipelineArtifactResponse(**item)
        for item in summary.get("artifacts", [])
    ]
    return AgentPipelineArtifactListResponse(
        scope_id=summary.get("scope_id", scope_id),
        user_id=owner_user_id,
        artifacts=artifacts,
        total=len(artifacts),
        created_at=summary.get("created_at"),
        updated_at=summary.get("updated_at"),
    )


# ============================================================================
# Assets Endpoints
# ============================================================================

@router.get(
    "/assets",
    response_model=AssetListResponse,
    summary="Get list of assets",
    description="Get list of all available assets with price data",
    tags=["Assets"]
)
async def get_assets(
    category: Optional[str] = Query(None, description="Filter by category (e.g., 'DeFi', 'Stablecoin')"),
    limit: Optional[int] = Query(50, description="Maximum number of assets to return"),
    exchange: Optional[str] = Query(None, description="Optional exchange source: 'phantom', 'spot', or 'futures'"),
):
    """
    Get list of assets with basic price information.
    
    **Parameters:**
    - `category` (optional): Filter by category
    - `limit` (optional): Maximum number of results (default: 50)
    
    **Returns:**
    - List of assets with symbol, name, price, and 24h change
    """
    try:
        assets = await _collect_tracked_assets(category=category, limit=limit, exchange=exchange)
        
        return {"assets": assets, "total": len(assets)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/assets/search",
    response_model=AssetSearchResponse,
    summary="Search tracked assets",
    description="Search tracked assets by symbol, name, or category",
    tags=["Assets"]
)
async def search_assets(
    q: str = Query(..., min_length=1, description="Search query such as BTC, Bitcoin, or DeFi"),
    limit: Optional[int] = Query(20, description="Maximum number of results to return"),
    exchange: Optional[str] = Query(None, description="Optional exchange source: 'phantom', 'spot', or 'futures'"),
):
    """Search the tracked asset universe for frontend pickers and discovery flows."""
    try:
        assets = await _collect_tracked_assets(limit=limit, query=q, exchange=exchange)
        return AssetSearchResponse(
            query=q,
            assets=[AssetListItem(**item) for item in assets],
            total=len(assets),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search_assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/assets/categories",
    response_model=AssetCategoryListResponse,
    summary="List available asset categories",
    description="List normalized categories currently represented in tracked assets",
    tags=["Assets"]
)
async def list_asset_categories(
    exchange: Optional[str] = Query(None, description="Optional exchange source: 'phantom', 'spot', or 'futures'"),
):
    """Return available categories for the current tracked asset universe."""
    try:
        assets = await _collect_tracked_assets(limit=len(settings.TRADING_ASSETS), exchange=exchange)
        stats = get_category_stats(assets)
        return AssetCategoryListResponse(
            categories=[
                {"name": name, "asset_count": count}
                for name, count in stats.items()
            ],
            total=len(stats),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in list_asset_categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/assets/categories/{category}",
    response_model=AssetCategoryAssetsResponse,
    summary="List assets for one category",
    description="Return tracked assets belonging to one normalized category",
    tags=["Assets"]
)
async def list_assets_by_category(
    category: str,
    limit: Optional[int] = Query(50, description="Maximum number of results to return"),
    exchange: Optional[str] = Query(None, description="Optional exchange source: 'phantom', 'spot', or 'futures'"),
):
    """Return assets belonging to one normalized category."""
    try:
        normalized_category = normalize_category(category)
        assets = await _collect_tracked_assets(
            category=normalized_category,
            limit=limit,
            exchange=exchange,
        )
        return AssetCategoryAssetsResponse(
            category=normalized_category,
            assets=[AssetListItem(**item) for item in assets],
            total=len(assets),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in list_assets_by_category: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/assets/supported",
    response_model=SupportedTradingAssetsResponse,
    summary="List supported tracked assets",
    description="Return the configured tracked asset symbols used by the backend",
    tags=["Assets"]
)
async def list_supported_trading_assets():
    """Return backend-configured tracked asset symbols for frontend initialization."""
    assets = [str(symbol).upper() for symbol in settings.TRADING_ASSETS]
    return SupportedTradingAssetsResponse(assets=assets, total=len(assets))


@router.get(
    "/assets/trending",
    response_model=TrendingAssetsResponse,
    summary="List lightweight trending tracked assets",
    description="Return a lightweight trending ranking built from tracked assets, volume, and 24h move",
    tags=["Assets"]
)
async def list_trending_assets(
    limit: Optional[int] = Query(10, description="Maximum number of trending assets to return"),
    exchange: Optional[str] = Query(None, description="Optional exchange source: 'phantom', 'spot', or 'futures'"),
):
    """Return a frontend-friendly trending list from the current tracked asset universe."""
    try:
        assets = await _collect_trending_assets(limit=limit, exchange=exchange)
        return TrendingAssetsResponse(
            assets=[TrendingAssetItem(**item) for item in assets],
            total=len(assets),
            ranking_method="tracked-asset score based on 24h volume and absolute 24h move",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in list_trending_assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/assets/{symbol}/summary",
    response_model=AssetSummaryResponse,
    summary="Get asset summary",
    description="Return a one-shot asset summary for frontend detail headers and overview cards",
    tags=["Assets"]
)
async def get_asset_summary(
    symbol: str,
    related_limit: Optional[int] = Query(3, description="Maximum number of related assets to include"),
):
    """Return a summary payload that combines key asset fields and a small related list."""
    try:
        from main import market_handler

        service = get_market_service()
        symbol = symbol.upper()

        coin_info = await service.get_coin_info(symbol)
        if not coin_info:
            raise HTTPException(status_code=404, detail=f"Asset '{symbol}' not found")

        price_update = market_handler.get_price(symbol)
        if not price_update:
            raise HTTPException(status_code=404, detail=f"Price data for '{symbol}' not available")

        contract_address = None
        if coin_info.contract_address:
            contract_address = list(coin_info.contract_address.values())[0]

        assets = await _collect_tracked_assets(limit=len(settings.TRADING_ASSETS))
        current_asset = next((item for item in assets if item["symbol"] == symbol), None)
        current_categories = set(current_asset.get("categories", [])) if current_asset else set(coin_info.categories or [])
        primary_category = get_primary_category(list(current_categories)) if current_categories else None

        related = []
        for asset in assets:
            if asset["symbol"] == symbol:
                continue
            other_categories = set(asset.get("categories", []))
            overlap = len(current_categories.intersection(other_categories))
            primary_match = bool(primary_category and primary_category in other_categories)
            if overlap == 0 and not primary_match:
                continue
            related.append((overlap, 1 if primary_match else 0, asset))

        related.sort(key=lambda item: (-item[0], -item[1], item[2]["symbol"]))
        limited_related = [
            AssetListItem(**item[2]) for item in related[: max(0, int(related_limit or 0))]
        ]

        return AssetSummaryResponse(
            symbol=symbol,
            name=coin_info.name,
            price=price_update.price,
            change_24h=price_update.change_24h,
            volume_24h=price_update.volume_24h,
            notional_volume_24h=price_update.notional_volume_24h,
            base_volume_24h=price_update.base_volume_24h,
            market_cap=price_update.market_cap,
            fdv=price_update.fdv,
            open_interest=price_update.open_interest,
            funding_rate=price_update.funding_rate,
            oracle_price=price_update.oracle_price,
            premium=price_update.premium,
            circulating_supply=price_update.circulating_supply,
            total_supply=price_update.total_supply,
            max_leverage=price_update.max_leverage,
            only_isolated=price_update.only_isolated,
            market_pair=price_update.market_pair,
            full_name=price_update.full_name,
            token_index=price_update.token_index,
            is_canonical=price_update.is_canonical,
            source_exchange=price_update.source_exchange,
            primary_category=primary_category,
            categories=coin_info.categories,
            description=coin_info.description,
            links={
                "website": coin_info.links.website if coin_info.links else None,
                "twitter": coin_info.links.twitter if coin_info.links else None,
                "telegram": coin_info.links.telegram if coin_info.links else None,
                "github": coin_info.links.github if coin_info.links else None,
                "explorer": coin_info.links.explorer if coin_info.links else None,
                "contract_address": contract_address,
            },
            related_assets=limited_related,
            last_updated=price_update.timestamp.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_asset_summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/assets/{symbol}",
    response_model=AssetDetailResponse,
    summary="Get asset detail",
    description="Get detailed information for a specific asset",
    tags=["Assets"]
)
async def get_asset_detail(symbol: str):
    """
    Get detailed information for a specific asset.
    
    **Parameters:**
    - `symbol`: Asset symbol (e.g., 'BTC', 'ETH', 'SOL')
    
    **Returns:**
    - Complete asset information including price, stats, description, and links
    """
    try:
        from main import market_handler
        
        service = get_market_service()
        
        symbol = symbol.upper()
        
        # Get coin info
        coin_info = await service.get_coin_info(symbol)
        if not coin_info:
            raise HTTPException(
                status_code=404,
                detail=f"Asset '{symbol}' not found"
            )
        
        # Get price data
        price_update = market_handler.get_price(symbol)
        if not price_update:
            raise HTTPException(
                status_code=404,
                detail=f"Price data for '{symbol}' not available"
            )
        
        # Get contract address (first one if multiple chains)
        contract_address = None
        if coin_info.contract_address:
            contract_address = list(coin_info.contract_address.values())[0]
        
        return {
            "symbol": symbol,
            "name": coin_info.name,
            "price": price_update.price,
            "change_24h": price_update.change_24h,
            "volume_24h": price_update.volume_24h,
            "notional_volume_24h": price_update.notional_volume_24h,
            "base_volume_24h": price_update.base_volume_24h,
            "high_24h": price_update.high_24h,
            "low_24h": price_update.low_24h,
            "market_cap": price_update.market_cap,
            "fdv": price_update.fdv,
            "open_interest": price_update.open_interest,
            "funding_rate": price_update.funding_rate,
            "oracle_price": price_update.oracle_price,
            "premium": price_update.premium,
            "circulating_supply": price_update.circulating_supply,
            "total_supply": price_update.total_supply,
            "max_leverage": price_update.max_leverage,
            "only_isolated": price_update.only_isolated,
            "market_pair": price_update.market_pair,
            "full_name": price_update.full_name,
            "token_index": price_update.token_index,
            "is_canonical": price_update.is_canonical,
            "source_exchange": price_update.source_exchange,
            "description": coin_info.description,
            "categories": coin_info.categories,
            "links": {
                "website": coin_info.links.website if coin_info.links else None,
                "twitter": coin_info.links.twitter if coin_info.links else None,
                "telegram": coin_info.links.telegram if coin_info.links else None,
                "github": coin_info.links.github if coin_info.links else None,
                "explorer": coin_info.links.explorer if coin_info.links else None,
                "contract_address": contract_address
            },
            "last_updated": price_update.timestamp.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_asset_detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/assets/{symbol}/related",
    response_model=RelatedAssetsResponse,
    summary="Get related tracked assets",
    description="Return tracked assets related by shared categories",
    tags=["Assets"]
)
async def get_related_assets(
    symbol: str,
    limit: Optional[int] = Query(5, description="Maximum number of related assets to return"),
):
    """Return related tracked assets using shared category overlap."""
    try:
        symbol = symbol.upper()
        assets = await _collect_tracked_assets(limit=len(settings.TRADING_ASSETS))
        current_asset = next((item for item in assets if item["symbol"] == symbol), None)
        if not current_asset:
            raise HTTPException(status_code=404, detail=f"Asset '{symbol}' not found")

        current_categories = set(current_asset.get("categories", []))
        primary_category = get_primary_category(list(current_categories)) if current_categories else None

        related = []
        for asset in assets:
            if asset["symbol"] == symbol:
                continue
            other_categories = set(asset.get("categories", []))
            overlap = sorted(current_categories.intersection(other_categories))
            score = len(overlap)
            primary_match = bool(primary_category and primary_category in other_categories)
            if score == 0 and not primary_match:
                continue
            related.append((score, 1 if primary_match else 0, asset))

        related.sort(key=lambda item: (-item[0], -item[1], item[2]["symbol"]))
        limited = [AssetListItem(**item[2]) for item in related[: max(0, int(limit or 0))]]

        return RelatedAssetsResponse(
            symbol=symbol,
            primary_category=primary_category,
            assets=limited,
            total=len(limited),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_related_assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/news/assets/{symbol}",
    response_model=AssetNewsResponse,
    summary="Get latest news snapshot for one tracked asset",
    description="Return a latest snapshot of asset-specific news using the existing news retrieval layer",
    tags=["Assets"]
)
async def get_asset_news(
    symbol: str,
    limit: int = Query(5, description="Maximum number of asset news items to return"),
):
    """Return a snapshot of the latest news for one tracked asset symbol."""
    from agents.tools.market.news_tools import get_news_client

    normalized_symbol = symbol.upper()
    response_timestamp = datetime.utcnow().isoformat()
    client = get_news_client()
    results = client.search_news_by_symbols([normalized_symbol], max_results=max(1, min(int(limit), 20)))
    asset_news = results.get(normalized_symbol, [])
    return AssetNewsResponse(
        timestamp=response_timestamp,
        symbol=normalized_symbol,
        news=[
            AssetNewsItem(
                **_enrich_news_item_timing(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("snippet"),
                        "date": item.get("date"),
                        "source": item.get("source"),
                        "symbol": normalized_symbol,
                        "detected_at": item.get("detected_at", response_timestamp),
                    },
                    response_timestamp,
                )
            )
            for item in asset_news
        ],
        total=len(asset_news),
    )


# ============================================================================
# OHLC Data Endpoint
# ============================================================================

@router.get(
    "/assets/{symbol}/ohlc",
    response_model=OHLCResponse,
    summary="Get OHLC data",
    description="Get OHLC (candlestick) data for charting",
    tags=["Chart Data"]
)
async def get_ohlc_data(
    symbol: str,
    interval: str = Query("1h", description="Interval (1m, 5m, 15m, 1h, 4h, 1d)"),
    limit: int = Query(100, description="Number of candles to return"),
    source: str = Query("auto", description="Data source: 'phantom_futures', 'phantom_spot', 'phantom', or 'auto'")
):
    """
    Get OHLC data for TradingView chart.
    
    **Parameters:**
    - `symbol`: Asset symbol (e.g., 'BTC', 'ETH')
    - `interval`: Candle interval (1m, 5m, 15m, 1h, 4h, 1d)
    - `limit`: Number of candles (default: 100, max: 1000)
    - `source`: Data source ('phantom_futures', 'phantom_spot', 'phantom', or 'auto')
    
    **Returns:**
    - OHLC data array for charting
    """
    try:
        # Validate interval
        valid_intervals = ["1m", "5m", "15m", "1h", "4h", "1d"]
        if interval not in valid_intervals:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid interval. Must be one of: {', '.join(valid_intervals)}"
            )
        
        # Validate limit
        if limit > 1000:
            limit = 1000
        
        symbol = symbol.upper()
        ohlc_data = []
        
        # Determine source
        normalized_source = str(source or "auto").strip().lower()
        if normalized_source == "auto":
            normalized_source = "phantom_futures"
        elif normalized_source == "phantom":
            normalized_source = "phantom_futures"
        elif normalized_source not in {"phantom_futures", "phantom_spot"}:
            raise HTTPException(
                status_code=400,
                detail="Invalid source. Must be one of: phantom_futures, phantom_spot, phantom, auto",
            )

        # Try to get from WebSocket handler first (real-time data)
        if normalized_source in {"phantom_futures", "phantom_spot"} and settings.uses_price_source("phantom"):
            from main import market_handler
            market_handler_exchange = normalized_source
            ohlc_data = market_handler.db.get_candles(symbol, market_handler_exchange, interval, limit=limit) if getattr(market_handler, "db", None) else []
            
        # If the live cache is missing or incomplete, fallback to Hyperliquid snapshots.
        if len(ohlc_data) < limit:
            logger.info("Not enough OHLC data from Phantom live handler, falling back to Hyperliquid snapshot")
            downloader = HyperliquidHistoryDownloader()
            ohlc_data = await downloader.download_history(
                symbol=symbol,
                interval=interval,
                limit=limit,
                market_source=normalized_source,
            )

            if not ohlc_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"OHLC data for '{symbol}' not available"
                )
        
        return {
            "symbol": symbol,
            "interval": interval,
            "data": ohlc_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_ohlc_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket Endpoint
# ============================================================================

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")


manager = ConnectionManager()


async def _collect_tracked_assets(
    *,
    category: Optional[str] = None,
    limit: Optional[int] = 50,
    query: Optional[str] = None,
    exchange: Optional[str] = None,
) -> List[dict]:
    """Build one filtered list from tracked backend assets."""
    from main import market_handler

    service = get_market_service()
    symbols = settings.TRADING_ASSETS
    max_items = len(symbols) if limit is None else max(0, int(limit))
    normalized_query = str(query or "").strip().lower()
    normalized_exchange = _normalize_exchange_filter(exchange)

    assets = []
    for symbol in symbols[:max_items]:
        try:
            coin_info = await service.get_coin_info(symbol)
            price_update = market_handler.get_price(symbol, exchange=normalized_exchange)

            if not coin_info or not price_update:
                continue

            if category and (not coin_info.categories or category not in coin_info.categories):
                continue

            asset = {
                "symbol": symbol,
                "name": coin_info.name,
                "price": price_update.price,
                "change_24h": price_update.change_24h,
                "categories": coin_info.categories,
            }

            if normalized_query:
                haystacks = [
                    asset["symbol"].lower(),
                    (asset["name"] or "").lower(),
                    " ".join(asset.get("categories", [])).lower(),
                ]
                if not any(normalized_query in haystack for haystack in haystacks):
                    continue

            assets.append(asset)
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            continue

    return assets


async def _collect_trending_assets(
    limit: Optional[int] = 10,
    exchange: Optional[str] = None,
) -> List[dict]:
    """Build a lightweight trending ranking from tracked assets."""
    from main import market_handler

    service = get_market_service()
    ranked = []
    max_items = max(0, int(limit or 0))
    normalized_exchange = _normalize_exchange_filter(exchange)

    for symbol in settings.TRADING_ASSETS:
        try:
            coin_info = await service.get_coin_info(symbol)
            price_update = market_handler.get_price(symbol, exchange=normalized_exchange)
            if not coin_info or not price_update:
                continue

            volume_24h = float(price_update.volume_24h or 0.0)
            abs_change = abs(float(price_update.change_24h or 0.0))
            score = (volume_24h / 1_000_000.0) + (abs_change * 10.0)

            reasons = []
            if volume_24h > 0:
                reasons.append("active 24h volume")
            if abs_change >= 5:
                reasons.append("strong 24h move")
            elif abs_change >= 2:
                reasons.append("meaningful 24h move")
            if "DeFi" in (coin_info.categories or []):
                reasons.append("DeFi exposure")
            if "Layer 1" in (coin_info.categories or []):
                reasons.append("Layer 1 exposure")

            ranked.append(
                {
                    "symbol": str(symbol).upper(),
                    "name": coin_info.name,
                    "price": price_update.price,
                    "change_24h": price_update.change_24h,
                    "categories": coin_info.categories,
                    "volume_24h": price_update.volume_24h,
                    "score": round(score, 4),
                    "reasons": reasons[:3],
                }
            )
        except Exception as e:
            logger.error(f"Error building trending data for {symbol}: {e}")
            continue

    ranked.sort(key=lambda item: (-item["score"], item["symbol"]))
    for idx, item in enumerate(ranked[:max_items], start=1):
        item["rank"] = idx
    return ranked[:max_items]


def _normalize_news_symbols(raw_symbols: Optional[str]) -> List[str]:
    """Normalize a comma-separated symbol list for news routes."""
    if not raw_symbols:
        return []
    return [
        symbol.strip().upper()
        for symbol in str(raw_symbols).split(",")
        if symbol.strip()
    ]


def _filter_news_message(message: dict, symbols: List[str], tail: int) -> dict:
    """Filter one internal news-monitor payload for the requested asset symbols."""
    news_items = list(message.get("news") or [])
    if symbols:
        filtered = [
            item
            for item in news_items
            if set(item.get("symbols") or []).intersection(symbols)
        ]
    else:
        filtered = news_items

    if tail > 0:
        filtered = filtered[-tail:]

    message_timestamp = message.get("timestamp") or datetime.utcnow().isoformat()
    normalized_items = [
        _enrich_news_item_timing(item, message_timestamp)
        for item in filtered
    ]

    return {
        **message,
        "timestamp": message_timestamp,
        "symbols": symbols,
        "count": len(normalized_items),
        "news": normalized_items,
    }


@router.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """
    WebSocket endpoint for real-time price updates.
    
    **Usage:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/ws/prices');
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data);
    };
    ```
    
    **Message Format:**
    ```json
    {
        "symbol": "BTC",
        "price": 65230.12,
        "change_24h": 2.45,
        "timestamp": "2024-01-01T00:00:00Z"
    }
    ```
    """
    await manager.connect(websocket)
    
    from main import market_handler
    
    # Subscribe to all price updates
    async def on_price_update(price_update):
        """Callback for price updates"""
        try:
            await manager.broadcast({
                "symbol": price_update.symbol,
                "price": price_update.price,
                "change_24h": price_update.change_24h,
                "volume_24h": price_update.volume_24h,
                "notional_volume_24h": price_update.notional_volume_24h,
                "base_volume_24h": price_update.base_volume_24h,
                "open_interest": price_update.open_interest,
                "funding_rate": price_update.funding_rate,
                "oracle_price": price_update.oracle_price,
                "premium": price_update.premium,
                "market_cap": price_update.market_cap,
                "fdv": price_update.fdv,
                "circulating_supply": price_update.circulating_supply,
                "total_supply": price_update.total_supply,
                "max_leverage": price_update.max_leverage,
                "only_isolated": price_update.only_isolated,
                "market_pair": price_update.market_pair,
                "full_name": price_update.full_name,
                "token_index": price_update.token_index,
                "is_canonical": price_update.is_canonical,
                "source_exchange": price_update.source_exchange,
                "timestamp": price_update.timestamp.isoformat()
            })
        except Exception as e:
            logger.error(f"Error in price update callback: {e}")
    
    # Subscribe to price updates
    market_handler.subscribe("price:*", on_price_update)
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/ws/news")
async def websocket_news(websocket: WebSocket):
    """WebSocket endpoint for live news updates derived from the news retrieval layer."""
    await websocket.accept()

    symbols = _normalize_news_symbols(websocket.query_params.get("symbols"))
    try:
        tail = max(1, min(int(websocket.query_params.get("tail", "5")), 20))
    except ValueError:
        tail = 5

    try:
        poll_interval = max(30, int(websocket.query_params.get("poll_interval", "300")))
    except ValueError:
        poll_interval = 300

    monitor = get_news_monitor()
    monitor.ensure_symbols(symbols)
    monitor.poll_interval = poll_interval

    if not monitor.running:
        await monitor.start()

    queue = monitor.subscribe()
    try:
        snapshot = monitor.get_asset_news_snapshot(symbols=symbols, tail=tail)
        snapshot_timestamp = datetime.utcnow().isoformat()
        normalized_snapshot = {
            symbol_key: [
                _enrich_news_item_timing(item, snapshot_timestamp)
                for item in items
            ]
            for symbol_key, items in snapshot.items()
        }
        await websocket.send_json(
            {
                "type": "news_snapshot",
                "timestamp": snapshot_timestamp,
                "symbols": symbols,
                "tail": tail,
                "news_by_symbol": normalized_snapshot,
            }
        )

        while True:
            queue_task = asyncio.create_task(queue.get())
            client_task = asyncio.create_task(websocket.receive_text())
            done, pending = await asyncio.wait(
                {queue_task, client_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()

            completed = next(iter(done))
            try:
                payload = completed.result()
            except WebSocketDisconnect:
                break

            if completed is client_task:
                if str(payload).strip().lower() == "ping":
                    await websocket.send_text("pong")
                continue

            await websocket.send_json(_filter_news_message(payload, symbols, tail))
    except WebSocketDisconnect:
        logger.info("News WebSocket client disconnected")
    except Exception as exc:
        logger.error(f"News WebSocket error: {exc}")
    finally:
        monitor.unsubscribe(queue)


# ============================================================================
# Agent Endpoints
# ============================================================================

@router.get(
    "/memory/health",
    response_model=MemoryHealthResponse,
    summary="Check Mem0 health",
    tags=["Memory"],
)
async def get_memory_health():
    """Return whether Mem0 is enabled and reachable."""
    client = get_mem0_client()

    if not client.enabled:
        return MemoryHealthResponse(
            enabled=False,
            healthy=False,
            base_url=client.base_url,
            detail="Mem0 is disabled",
        )

    try:
        await client.health_check()
        return MemoryHealthResponse(
            enabled=True,
            healthy=True,
            base_url=client.base_url,
            detail=None,
        )
    except Exception as exc:
        return MemoryHealthResponse(
            enabled=True,
            healthy=False,
            base_url=client.base_url,
            detail=str(exc),
        )


@router.get(
    "/memory/search",
    response_model=MemoryListResponse,
    summary="Search user memories",
    tags=["Memory"],
)
async def search_memory(
    user_id: str = Query(..., description="User ID"),
    query: str = Query(..., description="Semantic search query"),
    limit: int = Query(5, description="Maximum number of memories"),
):
    """Search Mem0 memories for one user."""
    try:
        memories = await get_mem0_client().search_memories(user_id=user_id, query=query, limit=limit)
        return MemoryListResponse(user_id=user_id, memories=memories, total=len(memories), query=query)
    except Exception as exc:
        _raise_mem0_http_error(exc)


@router.get(
    "/memory",
    response_model=MemoryListResponse,
    summary="List user memories",
    tags=["Memory"],
)
async def list_memory(user_id: str = Query(..., description="User ID")):
    """List all stored memories for one user."""
    try:
        memories = await get_mem0_client().get_all_memories(user_id=user_id)
        return MemoryListResponse(user_id=user_id, memories=memories, total=len(memories))
    except Exception as exc:
        _raise_mem0_http_error(exc)


@router.post(
    "/memory",
    response_model=MemoryCreateResponse,
    summary="Create a user memory",
    tags=["Memory"],
)
async def create_memory(request: MemoryCreateRequest):
    """Create a Mem0 memory through the backend API."""
    try:
        data = await get_mem0_client().add_memory(
            user_id=request.user_id,
            text=request.text,
            metadata=request.metadata,
        )
        return MemoryCreateResponse(success=True, user_id=request.user_id, data=data)
    except Exception as exc:
        _raise_mem0_http_error(exc)


@router.delete(
    "/memory/{memory_id}",
    response_model=MemoryDeleteResponse,
    summary="Delete one user memory",
    tags=["Memory"],
)
async def delete_memory(
    memory_id: str,
    user_id: str = Query(..., description="User ID"),
):
    """Delete one Mem0 memory by ID."""
    try:
        await get_mem0_client().delete_memory(user_id=user_id, memory_id=memory_id)
        return MemoryDeleteResponse(success=True, user_id=user_id, memory_id=memory_id)
    except Exception as exc:
        _raise_mem0_http_error(exc)


@router.delete(
    "/memory",
    response_model=MemoryDeleteResponse,
    summary="Delete all user memories",
    tags=["Memory"],
)
async def delete_all_memory(user_id: str = Query(..., description="User ID")):
    """Delete all Mem0 memories for one user."""
    try:
        await get_mem0_client().delete_all_memories(user_id=user_id)
        return MemoryDeleteResponse(success=True, user_id=user_id, deleted_all=True)
    except Exception as exc:
        _raise_mem0_http_error(exc)


@router.post(
    "/agent/uploads",
    response_model=AgentUploadResponse,
    summary="Upload temporary agent attachment",
    tags=["Agent"],
)
async def upload_agent_attachment(file: UploadFile = File(...)):
    """Upload a temporary image or PDF for agent multimodal input."""
    manager = get_upload_manager()

    try:
        record = await manager.save_upload(file)
        return AgentUploadResponse(
            file_id=record.file_id,
            filename=record.original_filename,
            content_type=record.content_type,
            kind=record.kind,
            size_bytes=record.size_bytes,
            expires_at=record.expires_at,
        )
    except UploadValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Error uploading agent attachment: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete(
    "/agent/uploads/{file_id}",
    response_model=AgentSessionDeleteResponse,
    summary="Delete temporary agent attachment",
    tags=["Agent"],
)
async def delete_agent_attachment(file_id: str):
    """Delete a temporary uploaded attachment."""
    deleted = get_upload_manager().delete(file_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Attachment '{file_id}' not found")

    return AgentUploadDeleteResponse(success=True, file_id=file_id)


@router.get(
    "/agent/sessions",
    response_model=AgentSessionListResponse,
    summary="List persisted assist sessions for the authenticated user",
    tags=["Agent"],
)
async def list_agent_sessions(
    user_id: Optional[str] = Query(default=None, description="Optional explicit user ID override"),
    authorization: Optional[str] = Header(default=None),
):
    """Return persisted assist sessions for one authenticated user."""
    auth_user = _get_authenticated_user(authorization)
    resolved_user_id = _require_resolved_user_id(
        _resolve_request_user_id(provided_user_id=user_id, auth_user=auth_user)
    )

    sessions = get_conversation_database().list_sessions(user_id=resolved_user_id)
    serialized = [_serialize_agent_session_summary(item) for item in sessions]
    return AgentSessionListResponse(sessions=serialized, total=len(serialized))


@router.get(
    "/agent/sessions/{scope_id}",
    response_model=AgentSessionDetailResponse,
    summary="Load one persisted assist session",
    tags=["Agent"],
)
async def get_agent_session(
    scope_id: str,
    user_id: Optional[str] = Query(default=None, description="Optional explicit user ID override"),
    authorization: Optional[str] = Header(default=None),
):
    """Return one persisted assist session for the authenticated user."""
    auth_user = _get_authenticated_user(authorization)
    resolved_user_id = _require_resolved_user_id(
        _resolve_request_user_id(provided_user_id=user_id, auth_user=auth_user)
    )

    session = get_conversation_database().get_session_record(scope_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{scope_id}' not found.")

    metadata = session.get("metadata", {}) or {}
    if metadata.get("user_id") != resolved_user_id:
        raise HTTPException(status_code=403, detail="Requested session does not belong to the authenticated user.")

    messages = [
        AgentSessionMessageResponse(
            role=item.get("role", "assistant"),
            content=item.get("content", ""),
            timestamp=item.get("timestamp", ""),
        )
        for item in session.get("messages", [])
    ]
    summary = _serialize_agent_session_summary(
        get_conversation_database().build_session_summary(scope_id, session)
    )
    return AgentSessionDetailResponse(
        **summary.model_dump(),
        messages=messages,
        metadata=metadata,
    )


@router.patch(
    "/agent/sessions/{scope_id}",
    response_model=AgentSessionSummaryResponse,
    summary="Rename one persisted assist session",
    tags=["Agent"],
)
async def update_agent_session(
    scope_id: str,
    request: AgentSessionUpdateRequest,
    user_id: Optional[str] = Query(default=None, description="Optional explicit user ID override"),
    authorization: Optional[str] = Header(default=None),
):
    """Rename one persisted assist session for the authenticated user."""
    auth_user = _get_authenticated_user(authorization)
    resolved_user_id = _require_resolved_user_id(
        _resolve_request_user_id(provided_user_id=user_id, auth_user=auth_user)
    )
    normalized_title = request.title.strip()
    if not normalized_title:
        raise HTTPException(status_code=400, detail="Session title cannot be empty.")

    database = get_conversation_database()
    session = database.get_session_record(scope_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{scope_id}' not found.")
    metadata = session.get("metadata", {}) or {}
    if metadata.get("user_id") != resolved_user_id:
        raise HTTPException(status_code=403, detail="Requested session does not belong to the authenticated user.")

    database.update_session_metadata(scope_id, {"title": normalized_title, "user_id": resolved_user_id})
    updated = database.get_session_record(scope_id)
    return _serialize_agent_session_summary(database.build_session_summary(scope_id, updated or session))


@router.delete(
    "/agent/sessions/{scope_id}",
    response_model=AgentSessionDeleteResponse,
    summary="Delete one persisted assist session",
    tags=["Agent"],
)
async def delete_agent_session(
    scope_id: str,
    user_id: Optional[str] = Query(default=None, description="Optional explicit user ID override"),
    authorization: Optional[str] = Header(default=None),
):
    """Delete one persisted assist session for the authenticated user."""
    auth_user = _get_authenticated_user(authorization)
    resolved_user_id = _require_resolved_user_id(
        _resolve_request_user_id(provided_user_id=user_id, auth_user=auth_user)
    )

    database = get_conversation_database()
    session = database.get_session_record(scope_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{scope_id}' not found.")
    metadata = session.get("metadata", {}) or {}
    if metadata.get("user_id") != resolved_user_id:
        raise HTTPException(status_code=403, detail="Requested session does not belong to the authenticated user.")

    database.delete_session(scope_id)
    return AgentSessionDeleteResponse(success=True, scope_id=scope_id)


@router.post(
    "/agent/chat",
    response_model=AgentChatResponse,
    summary="Chat with Rabit agent using temporary multimodal uploads",
    tags=["Agent"],
)
async def chat_with_agent(
    request: AgentChatRequest,
    authorization: Optional[str] = Header(default=None),
):
    """Chat with the Rabit agent using optional uploaded image/PDF attachments."""
    upload_manager = get_upload_manager()

    try:
        auth_user = _get_authenticated_user(authorization)
        await _require_contract_chat_ready(auth_user)
        attachments = upload_manager.resolve_attachments(request.attachment_ids)
        resolved_user_id = _resolve_request_user_id(
            provided_user_id=request.user_id,
            auth_user=auth_user,
        )
        tool_preferences = request.tool_preferences.model_dump() if request.tool_preferences else None
        normalized_tool_preferences = normalize_tool_preferences(tool_preferences)
        effective_memory_user_id = (
            resolved_user_id if normalized_tool_preferences.get("memory_enabled", True) else None
        )
        execution_gate = normalize_execution_gate(
            request.execution_gate.model_dump() if request.execution_gate else None
        )
        agent = get_agent(scope_id=request.scope_id, user_id=effective_memory_user_id)
        response = await agent.process_trading_query(
            request.message,
            attachments=attachments,
            conversation_style=request.conversation_style,
            trading_style=request.trading_style,
            market_context=request.market_context.model_dump() if request.market_context else None,
            execution_gate=execution_gate,
            tool_preferences=tool_preferences,
        )
        _persist_agent_session_metadata(
            scope_id=request.scope_id,
            request=request,
            user_id=resolved_user_id,
        )

        return AgentChatResponse(
            response=response,
            scope_id=request.scope_id,
            user_id=resolved_user_id,
            conversation_style=_serialize_conversation_style(agent.last_conversation_style),
            trading_style=_serialize_trading_style(agent.last_trading_style),
            market_context=_serialize_market_context(getattr(agent, "last_market_context", request.market_context)),
            execution_gate=_serialize_execution_gate(
                getattr(
                    agent,
                    "last_execution_gate",
                    execution_gate,
                )
            ),
            tool_preferences=_serialize_tool_preferences(
                getattr(
                    agent,
                    "last_tool_preferences",
                    tool_preferences,
                )
            ),
            attachment_ids=request.attachment_ids,
            intent=_serialize_agent_intent(agent),
            agent_pipeline=_serialize_agent_pipeline(agent),
            session_cost=_serialize_session_cost(
                getattr(agent, "last_session_cost_summary", None)
            ),
            service_cost=_build_service_cost_summary(
                scope_id=request.scope_id,
                user_id=resolved_user_id,
                session_cost=getattr(agent, "last_session_cost_summary", None),
                monitoring_cost=(
                    getattr(agent, "last_service_cost_summary", {}) or {}
                ).get("monitoring_cost")
                if getattr(agent, "last_service_cost_summary", None)
                else None,
            ),
        )
    except UploadValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in agent chat endpoint: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/agent/chat/stream",
    summary="Stream Rabit agent chat events over SSE",
    tags=["Agent"],
)
async def stream_chat_with_agent(
    request: AgentChatRequest,
    authorization: Optional[str] = Header(default=None),
):
    """Stream agent output, thinking summary, plan, hint, and error events over SSE."""

    auth_user = _get_authenticated_user(authorization)
    await _require_contract_chat_ready(auth_user)
    resolved_user_id = _resolve_request_user_id(
        provided_user_id=request.user_id,
        auth_user=auth_user,
    )

    async def event_generator():
        queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

        async def emit(event_name: str, payload: dict):
            await queue.put(_format_sse(event_name, payload))

        async def run_agent():
            agent = None
            try:
                upload_manager = get_upload_manager()
                attachments = upload_manager.resolve_attachments(request.attachment_ids)
                tool_preferences = request.tool_preferences.model_dump() if request.tool_preferences else None
                normalized_tool_preferences = normalize_tool_preferences(tool_preferences)
                effective_memory_user_id = (
                    resolved_user_id if normalized_tool_preferences.get("memory_enabled", True) else None
                )
                execution_gate = normalize_execution_gate(
                    request.execution_gate.model_dump() if request.execution_gate else None
                )
                agent = get_agent(scope_id=request.scope_id, user_id=effective_memory_user_id)

                response = await agent.process_stream(
                    request.message,
                    event_emitter=emit,
                    use_tools=True,
                    attachments=attachments,
                    conversation_style=request.conversation_style,
                    trading_style=request.trading_style,
                    market_context=request.market_context.model_dump() if request.market_context else None,
                    execution_gate=execution_gate,
                    tool_preferences=tool_preferences,
                )
                _persist_agent_session_metadata(
                    scope_id=request.scope_id,
                    request=request,
                    user_id=resolved_user_id,
                )

                await emit(
                    "done",
                    {
                        "type": "done",
                        "status": "completed",
                        "response": response,
                        "scope_id": request.scope_id,
                        "user_id": resolved_user_id,
                        "conversation_style": _serialize_conversation_style(
                            getattr(agent, "last_conversation_style", request.conversation_style)
                        ),
                        "trading_style": _serialize_trading_style(
                            getattr(agent, "last_trading_style", request.trading_style)
                        ),
                        "market_context": _serialize_market_context(
                            getattr(
                                agent,
                                "last_market_context",
                                request.market_context.model_dump() if request.market_context else None,
                            )
                        ),
                        "execution_gate": _serialize_execution_gate(
                            getattr(
                                agent,
                                "last_execution_gate",
                                execution_gate,
                            )
                        ),
                        "tool_preferences": _serialize_tool_preferences(
                            getattr(agent, "last_tool_preferences", tool_preferences)
                        ),
                        "attachment_ids": request.attachment_ids,
                        "intent": _serialize_agent_intent(agent),
                        "agent_pipeline": _serialize_agent_pipeline(agent),
                        "session_cost": _serialize_session_cost(
                            getattr(agent, "last_session_cost_summary", None)
                        ),
                        "service_cost": _build_service_cost_summary(
                            scope_id=request.scope_id,
                            user_id=resolved_user_id,
                            session_cost=getattr(agent, "last_session_cost_summary", None),
                            monitoring_cost=(
                                getattr(agent, "last_service_cost_summary", {}) or {}
                            ).get("monitoring_cost")
                            if getattr(agent, "last_service_cost_summary", None)
                            else None,
                        ),
                    },
                )
            except UploadValidationError as exc:
                await emit(
                    "error",
                    {
                        "type": "error",
                        "source": "request",
                        "message": str(exc),
                        "details": {},
                    },
                )
                await emit(
                    "done",
                    {
                        "type": "done",
                        "status": "failed",
                        "conversation_style": _serialize_conversation_style(
                            getattr(agent, "last_conversation_style", request.conversation_style)
                        ),
                        "trading_style": _serialize_trading_style(
                            getattr(agent, "last_trading_style", request.trading_style)
                        ),
                        "market_context": _serialize_market_context(
                            getattr(
                                agent,
                                "last_market_context",
                                request.market_context.model_dump() if request.market_context else None,
                            )
                        ),
                        "execution_gate": _serialize_execution_gate(
                            getattr(
                                agent,
                                "last_execution_gate",
                                execution_gate if 'execution_gate' in locals() else None,
                            )
                        ),
                        "intent": _serialize_agent_intent(agent),
                        "agent_pipeline": _serialize_agent_pipeline(agent),
                        "session_cost": _serialize_session_cost(
                            getattr(agent, "last_session_cost_summary", None)
                        ),
                        "service_cost": _build_service_cost_summary(
                            scope_id=request.scope_id,
                            user_id=resolved_user_id,
                            session_cost=getattr(agent, "last_session_cost_summary", None),
                            monitoring_cost=(
                                getattr(agent, "last_service_cost_summary", {}) or {}
                            ).get("monitoring_cost")
                            if getattr(agent, "last_service_cost_summary", None)
                            else None,
                        ),
                    },
                )
            except Exception as exc:
                logger.error(f"Error in streaming agent chat endpoint: {exc}")
                await emit(
                    "error",
                    {
                        "type": "error",
                        "source": "agent",
                        "message": str(exc),
                        "details": {
                            "error_type": type(exc).__name__,
                        },
                    },
                )
                await emit(
                    "done",
                    {
                        "type": "done",
                        "status": "failed",
                        "conversation_style": _serialize_conversation_style(
                            getattr(agent, "last_conversation_style", request.conversation_style)
                        ),
                        "trading_style": _serialize_trading_style(
                            getattr(agent, "last_trading_style", request.trading_style)
                        ),
                        "market_context": _serialize_market_context(
                            getattr(
                                agent,
                                "last_market_context",
                                request.market_context.model_dump() if request.market_context else None,
                            )
                        ),
                        "execution_gate": _serialize_execution_gate(
                            getattr(
                                agent,
                                "last_execution_gate",
                                execution_gate if 'execution_gate' in locals() else None,
                            )
                        ),
                        "intent": _serialize_agent_intent(agent),
                        "agent_pipeline": _serialize_agent_pipeline(agent),
                        "session_cost": _serialize_session_cost(
                            getattr(agent, "last_session_cost_summary", None)
                        ),
                        "service_cost": _build_service_cost_summary(
                            scope_id=request.scope_id,
                            user_id=resolved_user_id,
                            session_cost=getattr(agent, "last_session_cost_summary", None),
                            monitoring_cost=(
                                getattr(agent, "last_service_cost_summary", {}) or {}
                            ).get("monitoring_cost")
                            if getattr(agent, "last_service_cost_summary", None)
                            else None,
                        ),
                    },
                )
            finally:
                await queue.put(None)

        task = asyncio.create_task(run_agent())
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield item
        finally:
            if not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

    import contextlib

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================================
# Health Check
# ============================================================================

@router.get(
    "/health",
    summary="Health check",
    description="Check API health status",
    tags=["System"]
)
async def health_check():
    """
    Health check endpoint.
    
    **Returns:**
    - API status and version
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "Rabit Backend API"
    }



# ============================================
# OpenRouter Models Endpoints
# ============================================

@router.get("/models", response_model=ModelsListResponse, tags=["Models"])
async def list_models(
    require_tools: bool = False,
    require_reasoning: bool = False,
    min_context: Optional[int] = None,
    max_input_price: Optional[float] = None,
    max_output_price: Optional[float] = None,
    provider: Optional[str] = None,
    enabled_only: bool = True,
    refresh: bool = False
):
    """
    List available OpenRouter models with filtering
    
    Query Parameters:
    - require_tools: Only models that support tool calling
    - require_reasoning: Only models that support reasoning
    - min_context: Minimum context length
    - max_input_price: Maximum input price per 1M tokens (USD)
    - max_output_price: Maximum output price per 1M tokens (USD)
    - provider: Filter by provider (e.g., 'anthropic', 'openai', 'google')
    - enabled_only: Only return enabled models (default: true)
    - refresh: Force refresh from OpenRouter API (default: false)
    """
    try:
        from agents.openrouter import get_openrouter_models
        
        models_manager = get_openrouter_models()
        
        # Fetch models (with cache)
        await models_manager.fetch_models(force_refresh=refresh)
        
        # Filter models
        filtered_models = models_manager.filter_models(
            require_tools=require_tools,
            require_reasoning=require_reasoning,
            min_context=min_context,
            max_input_price=max_input_price,
            max_output_price=max_output_price,
            provider=provider,
            enabled_only=enabled_only
        )
        onchain_snapshot = await _get_onchain_model_registry_snapshot(
            force_refresh=refresh,
        )
        
        # Get stats
        stats = models_manager.get_stats()
        
        return ModelsListResponse(
            models=[
                _serialize_model_info_response(m, onchain_snapshot)
                for m in filtered_models
            ],
            total=len(filtered_models),
            enabled=len([m for m in filtered_models if m.enabled]),
            disabled=len([m for m in filtered_models if not m.enabled]),
            last_updated=stats.get("last_updated"),
            onchain_available=onchain_snapshot.available,
            onchain_registered_models=onchain_snapshot.total_registered,
            onchain_active_models=onchain_snapshot.total_active,
            onchain_verified_models=onchain_snapshot.total_verified,
            onchain_last_updated=onchain_snapshot.last_updated,
            onchain_error=onchain_snapshot.error,
        )
    
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/stats", response_model=ModelStatsResponse, tags=["Models"])
async def get_models_stats():
    """Get statistics about available models"""
    try:
        from agents.openrouter import get_openrouter_models
        
        models_manager = get_openrouter_models()
        
        # Fetch models (uses cache automatically)
        await models_manager.fetch_models()
        
        stats = models_manager.get_stats()
        onchain_snapshot = await _get_onchain_model_registry_snapshot()
        
        return ModelStatsResponse(
            **stats,
            onchain_available=onchain_snapshot.available,
            onchain_registered_models=onchain_snapshot.total_registered,
            onchain_active_models=onchain_snapshot.total_active,
            onchain_verified_models=onchain_snapshot.total_verified,
            onchain_last_updated=onchain_snapshot.last_updated,
            onchain_error=onchain_snapshot.error,
        )
    
    except Exception as e:
        logger.error(f"Error getting model stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_id:path}", response_model=ModelInfoResponse, tags=["Models"])
async def get_model_info(model_id: str):
    """Get information about a specific model"""
    try:
        from agents.openrouter import get_openrouter_models
        
        models_manager = get_openrouter_models()
        
        # Fetch models (uses cache automatically)
        await models_manager.fetch_models()
        
        model = models_manager.get_model(model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
        
        onchain_snapshot = await _get_onchain_model_registry_snapshot()
        return _serialize_model_info_response(model, onchain_snapshot)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/toggle", tags=["Models"])
async def toggle_model(request: ModelToggleRequest):
    """Enable or disable a model"""
    try:
        from agents.openrouter import get_openrouter_models
        
        models_manager = get_openrouter_models()
        
        # Fetch models (uses cache automatically)
        await models_manager.fetch_models()
        
        model = models_manager.get_model(request.model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model '{request.model_id}' not found")
        
        if request.enabled:
            models_manager.enable_model(request.model_id)
        else:
            models_manager.disable_model(request.model_id)
        
        return {
            "success": True,
            "model_id": request.model_id,
            "enabled": request.enabled,
            "message": f"Model {'enabled' if request.enabled else 'disabled'} successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/models/providers", tags=["Models"])
async def list_providers():
    """Get list of all providers"""
    try:
        from agents.openrouter import get_openrouter_models
        
        models_manager = get_openrouter_models()
        
        # Fetch models (uses cache automatically)
        await models_manager.fetch_models()
        
        providers = models_manager.get_providers()
        
        return {
            "providers": providers,
            "total": len(providers)
        }
    
    except Exception as e:
        logger.error(f"Error listing providers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/grouped", tags=["Models"])
async def get_models_grouped(
    enabled_only: bool = True,
    require_tools: bool = False,
    require_reasoning: bool = False
):
    """
    Get models grouped by provider
    
    Query Parameters:
    - enabled_only: Only include enabled models (default: true)
    - require_tools: Only models with tool calling support
    - require_reasoning: Only models with reasoning support
    """
    try:
        from agents.openrouter import get_openrouter_models
        
        models_manager = get_openrouter_models()
        
        # Fetch models (uses cache automatically)
        await models_manager.fetch_models()
        onchain_snapshot = await _get_onchain_model_registry_snapshot()
        
        # Filter first if needed
        if require_tools or require_reasoning:
            filtered = models_manager.filter_models(
                require_tools=require_tools,
                require_reasoning=require_reasoning,
                enabled_only=enabled_only
            )
            # Manually group filtered models
            grouped = {}
            for model in filtered:
                provider = model.provider
                if provider not in grouped:
                    grouped[provider] = []
                grouped[provider].append(
                    _serialize_model_info_response(model, onchain_snapshot)
                )
            grouped = dict(sorted(grouped.items()))
        else:
            # Use built-in grouping
            grouped_models = models_manager.get_models_by_provider(enabled_only=enabled_only)
            grouped = {
                provider: [
                    _serialize_model_info_response(m, onchain_snapshot)
                    for m in models
                ]
                for provider, models in grouped_models.items()
            }
        
        # Calculate stats per provider
        provider_stats = {}
        for provider, models in grouped.items():
            provider_stats[provider] = {
                "total": len(models),
                "with_tools": len([m for m in models if m.supports_tools]),
                "with_reasoning": len([m for m in models if m.supports_reasoning])
            }
        
        return {
            "grouped": grouped,
            "provider_stats": provider_stats,
            "total_providers": len(grouped),
            "onchain_available": onchain_snapshot.available,
            "onchain_registered_models": onchain_snapshot.total_registered,
            "onchain_active_models": onchain_snapshot.total_active,
            "onchain_verified_models": onchain_snapshot.total_verified,
            "onchain_last_updated": onchain_snapshot.last_updated,
            "onchain_error": onchain_snapshot.error,
        }
    
    except Exception as e:
        logger.error(f"Error grouping models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/models/database/stats", tags=["Models"])
async def get_database_stats():
    """Get database statistics"""
    try:
        from agents.openrouter import get_models_database
        
        db = get_models_database()
        stats = db.get_stats()
        onchain_snapshot = await _get_onchain_model_registry_snapshot()
        
        return {
            **stats,
            "onchain_available": onchain_snapshot.available,
            "onchain_registered_models": onchain_snapshot.total_registered,
            "onchain_active_models": onchain_snapshot.total_active,
            "onchain_verified_models": onchain_snapshot.total_verified,
            "onchain_last_updated": onchain_snapshot.last_updated,
            "onchain_error": onchain_snapshot.error,
        }
    
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/database/refresh", tags=["Models"])
async def refresh_database():
    """Force refresh database from OpenRouter API"""
    try:
        from agents.openrouter import get_openrouter_models
        
        models_manager = get_openrouter_models()
        
        # Force refresh from API
        models = await models_manager.fetch_models(force_refresh=True)
        
        return {
            "success": True,
            "message": "Database refreshed successfully",
            "total_models": len(models),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error refreshing database: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/models/database/clear", tags=["Models"])
async def clear_database():
    """Clear all models from database (will be refetched on next request)"""
    try:
        from agents.openrouter import get_models_database
        
        db = get_models_database()
        db.clear()
        
        return {
            "success": True,
            "message": "Database cleared successfully"
        }
    
    except Exception as e:
        logger.error(f"Error clearing database: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
