from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.core.settings import settings


class PaymentCheckoutError(RuntimeError):
    pass


@dataclass
class CheckoutSession:
    provider: str
    provider_reference: str
    checkout_url: str | None
    expires_at: datetime | None
    raw_payload: dict[str, Any]


def _normalize_provider(payment_provider: str | None = None) -> str:
    provider = (payment_provider or getattr(settings, "PAYMENT_PROVIDER", "") or "manual").strip().lower()
    return provider or "manual"


def _build_manual_checkout_url(*, billing_request_id: int, tenant_id: int, provider_reference: str) -> str:
    base = (getattr(settings, "PAYMENT_CHECKOUT_BASE_URL", "") or "").strip().rstrip("/")
    if base:
        return f"{base}/billing/{billing_request_id}/checkout?tenant_id={tenant_id}&ref={provider_reference}"
    return f"https://checkout.local/billing/{billing_request_id}?tenant_id={tenant_id}&ref={provider_reference}"


def create_checkout_session(
    *,
    billing_request_id: int,
    tenant_id: int,
    amount_cents: int,
    currency: str,
    payment_method: str,
    requested_plan_type: str,
    payment_provider: str | None = None,
) -> CheckoutSession:
    if amount_cents <= 0:
        raise PaymentCheckoutError("amount_cents inválido para checkout.")

    if payment_method not in {"pix", "credit_card", "debit_card"}:
        raise PaymentCheckoutError("payment_method inválido para checkout.")

    provider = _normalize_provider(payment_provider)

    if provider == "manual":
        provider_reference = f"manual_{billing_request_id}_{uuid4().hex[:12]}"
        checkout_url = _build_manual_checkout_url(
            billing_request_id=billing_request_id,
            tenant_id=tenant_id,
            provider_reference=provider_reference,
        )
        return CheckoutSession(
            provider=provider,
            provider_reference=provider_reference,
            checkout_url=checkout_url,
            expires_at=None,
            raw_payload={
                "mode": "manual_foundation",
                "billing_request_id": billing_request_id,
                "tenant_id": tenant_id,
                "amount_cents": amount_cents,
                "currency": currency,
                "payment_method": payment_method,
                "requested_plan_type": requested_plan_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    raise PaymentCheckoutError(
        f"Provider de pagamento não suportado ainda: {provider}. "
        "Implemente o adaptador real antes de habilitar em produção."
    )
