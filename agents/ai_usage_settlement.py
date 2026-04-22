"""Bridge backend USD service-cost summaries into Rabit on-chain AI usage previews."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional

from config.settings import settings
from contract import (
    derive_delegated_signer_pda,
    derive_model_registry_pda,
    derive_spending_profile_pda,
    load_deployment,
)


def wallet_address_from_user_id(user_id: Optional[str]) -> Optional[str]:
    """Extract a wallet address from the canonical wallet-scoped backend user_id."""
    if not user_id:
        return None
    prefix = "wallet:"
    if not str(user_id).startswith(prefix):
        return None
    wallet_address = str(user_id)[len(prefix):].strip()
    return wallet_address or None


def _decimal(value: Any) -> Decimal:
    """Convert numeric-like values into Decimal safely."""
    try:
        return Decimal(str(value or 0))
    except Exception:
        return Decimal("0")


def _round_usd(value: Any) -> float:
    """Round USD-like values to stable API precision."""
    return round(float(value or 0.0), 10)


def _calculate_bps(amount: int, bps: int) -> int:
    """Mirror the contract's integer basis-points calculation."""
    return (int(amount) * int(bps)) // 10000


def _usd_to_payment_units(usd_amount: float, *, usd_per_token: float, decimals: int) -> int:
    """Convert a USD amount into integer payment-token units."""
    if usd_amount <= 0:
        return 0

    token_price = _decimal(usd_per_token)
    if token_price <= 0:
        raise ValueError("RABIT_AI_USAGE_PAYMENT_TOKEN_USD_PRICE must be greater than zero.")

    multiplier = Decimal(10) ** int(decimals)
    raw_units = (_decimal(usd_amount) / token_price) * multiplier
    return int(raw_units.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def build_onchain_ai_usage_preview(
    *,
    scope_id: str,
    user_id: Optional[str],
    session_cost: Optional[Dict[str, Any]],
    monitoring_cost: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Build a contract-aligned AI-usage settlement preview from backend USD summaries."""
    if not session_cost and not monitoring_cost:
        return None

    deployment = load_deployment(settings.RABIT_CONTRACT_CLUSTER)
    resolved_user_id = user_id or (session_cost or {}).get("user_id") or (monitoring_cost or {}).get("user_id")
    owner_wallet_address = wallet_address_from_user_id(resolved_user_id)

    model_cost_usd = _round_usd((session_cost or {}).get("estimated_cost_usd"))
    service_cost_usd = _round_usd((monitoring_cost or {}).get("total_cost_usd"))
    total_cost_usd = _round_usd(model_cost_usd + service_cost_usd)
    total_tokens = int((session_cost or {}).get("total_tokens") or 0)
    model_ids = sorted({str(value) for value in ((session_cost or {}).get("model_ids") or []) if value})
    resolved_model_id = model_ids[0] if len(model_ids) == 1 else None

    payment_token_symbol = settings.RABIT_AI_USAGE_PAYMENT_TOKEN_SYMBOL
    payment_mint = settings.RABIT_AI_USAGE_PAYMENT_MINT or None
    payment_decimals = settings.RABIT_AI_USAGE_PAYMENT_MINT_DECIMALS
    payment_token_usd_price = settings.RABIT_AI_USAGE_PAYMENT_TOKEN_USD_PRICE
    markup_bps = settings.RABIT_AI_USAGE_DEFAULT_MARKUP_BPS
    platform_fee_bps = settings.RABIT_AI_USAGE_PLATFORM_FEE_BPS
    usage_type = settings.RABIT_AI_USAGE_DEFAULT_USAGE_TYPE

    conversion_error: Optional[str] = None
    try:
        base_cost_units = _usd_to_payment_units(
            model_cost_usd,
            usd_per_token=payment_token_usd_price,
            decimals=payment_decimals,
        )
        service_cost_units = _usd_to_payment_units(
            service_cost_usd,
            usd_per_token=payment_token_usd_price,
            decimals=payment_decimals,
        )
    except Exception as exc:
        conversion_error = str(exc)
        base_cost_units = 0
        service_cost_units = 0

    chargeable_cost_units = base_cost_units + service_cost_units
    markup_amount_units = _calculate_bps(chargeable_cost_units, markup_bps)
    cost_after_markup_units = chargeable_cost_units + markup_amount_units
    platform_fee_amount_units = _calculate_bps(cost_after_markup_units, platform_fee_bps)
    total_charged_units = cost_after_markup_units + platform_fee_amount_units

    notes = []
    spending_profile_pda = None
    delegated_signer_pda = None
    model_registry_pda = None
    if owner_wallet_address:
        try:
            spending_profile_pda, _ = derive_spending_profile_pda(
                owner_wallet_address,
                cluster=deployment.cluster,
                program_id=deployment.program_id,
            )
            if deployment.backend_authority_wallet:
                delegated_signer_pda, _ = derive_delegated_signer_pda(
                    owner_wallet_address,
                    deployment.backend_authority_wallet,
                    cluster=deployment.cluster,
                    program_id=deployment.program_id,
                )
        except Exception:
            notes.append("Resolved wallet-style user_id is not a valid Solana pubkey, so PDA previews are unavailable.")
            owner_wallet_address = None

    if resolved_model_id:
        try:
            model_registry_pda, _ = derive_model_registry_pda(
                resolved_model_id,
                cluster=deployment.cluster,
                program_id=deployment.program_id,
            )
        except Exception as exc:
            notes.append(f"Unable to derive model registry PDA: {exc}")

    if not owner_wallet_address:
        notes.append("user_id is not wallet-derived, so spending-profile PDAs cannot be derived yet.")
    if len(model_ids) != 1:
        notes.append("This scope contains multiple models or no model ID, so one record_ai_usage instruction cannot be built yet.")
    if not payment_mint:
        notes.append("Payment mint is not configured in backend settings, so this is a quote-level preview only.")
    if conversion_error:
        notes.append(conversion_error)
    if deployment.backend_authority_wallet:
        notes.append("Delegated-signer PDA shown here is only a preview; the on-chain delegated signer must already exist and be approved.")

    instruction_buildable = bool(
        owner_wallet_address
        and resolved_model_id
        and payment_mint
        and not conversion_error
    )
    instruction_name = (
        "record_ai_usage_with_delegation"
        if instruction_buildable and deployment.backend_authority_wallet
        else "record_ai_usage"
        if instruction_buildable
        else None
    )

    return {
        "scope_id": scope_id,
        "user_id": resolved_user_id,
        "cluster": deployment.cluster,
        "program_id": deployment.program_id,
        "config_pda": deployment.config_pda,
        "fee_recipient_pda": deployment.fee_recipient_pda,
        "backend_authority_wallet": deployment.backend_authority_wallet,
        "owner_wallet_address": owner_wallet_address,
        "spending_profile_pda": spending_profile_pda,
        "delegated_signer_pda": delegated_signer_pda,
        "payment_mint": payment_mint,
        "payment_token_symbol": payment_token_symbol,
        "payment_mint_decimals": payment_decimals,
        "payment_token_usd_price": payment_token_usd_price,
        "usage_type": usage_type,
        "tokens_used": total_tokens,
        "model_ids": model_ids,
        "model_id": resolved_model_id,
        "model_registry_pda": model_registry_pda,
        "model_cost_usd": model_cost_usd,
        "service_cost_usd": service_cost_usd,
        "total_cost_usd": total_cost_usd,
        "base_cost_units": base_cost_units,
        "service_cost_units": service_cost_units,
        "chargeable_cost_units": chargeable_cost_units,
        "markup_bps": markup_bps,
        "markup_amount_units": markup_amount_units,
        "platform_fee_bps": platform_fee_bps,
        "platform_fee_amount_units": platform_fee_amount_units,
        "total_charged_units": total_charged_units,
        "instruction_buildable": instruction_buildable,
        "instruction_name": instruction_name,
        "preview_mode": "aggregate_scope_preview",
        "notes": notes,
    }


__all__ = ["build_onchain_ai_usage_preview"]
