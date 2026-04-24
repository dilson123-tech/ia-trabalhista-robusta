from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import requests

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


def _create_manual_checkout(
    *,
    billing_request_id: int,
    tenant_id: int,
    amount_cents: int,
    currency: str,
    payment_method: str,
    requested_plan_type: str,
) -> CheckoutSession:
    provider_reference = f"manual_{billing_request_id}_{uuid4().hex[:12]}"
    checkout_url = _build_manual_checkout_url(
        billing_request_id=billing_request_id,
        tenant_id=tenant_id,
        provider_reference=provider_reference,
    )
    return CheckoutSession(
        provider="manual",
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


def _asaas_billing_type(payment_method: str) -> str:
    if payment_method == "pix":
        return "PIX"
    if payment_method == "credit_card":
        return "CREDIT_CARD"
    if payment_method == "debit_card":
        return "UNDEFINED"
    raise PaymentCheckoutError("payment_method inválido para Asaas.")


def _asaas_headers() -> dict[str, str]:
    api_key = (getattr(settings, "ASAAS_API_KEY", "") or "").strip()
    if not api_key:
        raise PaymentCheckoutError("ASAAS_API_KEY não configurada.")

    return {
        "accept": "application/json",
        "content-type": "application/json",
        "access_token": api_key,
    }


def _asaas_base_url() -> str:
    return (getattr(settings, "ASAAS_BASE_URL", "") or "https://api-sandbox.asaas.com/v3").strip().rstrip("/")


def _create_asaas_customer(*, tenant_id: int) -> dict[str, Any]:
    url = f"{_asaas_base_url()}/customers"
    payload = {
        "name": f"Tenant {tenant_id}",
        "email": f"tenant-{tenant_id}@checkout.local",
    }

    try:
        response = requests.post(url, headers=_asaas_headers(), json=payload, timeout=20)
    except requests.RequestException as exc:
        raise PaymentCheckoutError(f"Falha ao criar customer Asaas: {exc}") from exc

    if response.status_code >= 400:
        raise PaymentCheckoutError(f"Erro Asaas ao criar customer: {response.status_code} {response.text}")

    return response.json()


def _create_asaas_checkout(
    *,
    billing_request_id: int,
    tenant_id: int,
    amount_cents: int,
    currency: str,
    payment_method: str,
    requested_plan_type: str,
) -> CheckoutSession:
    if currency.upper() != "BRL":
        raise PaymentCheckoutError("Asaas suporta apenas BRL neste fluxo inicial.")

    customer = _create_asaas_customer(tenant_id=tenant_id)
    customer_id = customer.get("id")
    if not customer_id:
        raise PaymentCheckoutError("Asaas não retornou customer id.")

    url = f"{_asaas_base_url()}/payments"
    payload = {
        "customer": customer_id,
        "billingType": _asaas_billing_type(payment_method),
        "value": round(amount_cents / 100, 2),
        "dueDate": datetime.now(timezone.utc).date().isoformat(),
        "description": f"IA Trabalhista Robusta - plano {requested_plan_type} - billing request {billing_request_id}",
        "externalReference": str(billing_request_id),
    }

    try:
        response = requests.post(url, headers=_asaas_headers(), json=payload, timeout=20)
    except requests.RequestException as exc:
        raise PaymentCheckoutError(f"Falha ao criar pagamento Asaas: {exc}") from exc

    if response.status_code >= 400:
        raise PaymentCheckoutError(f"Erro Asaas ao criar pagamento: {response.status_code} {response.text}")

    data = response.json()
    provider_reference = data.get("id")
    checkout_url = data.get("invoiceUrl") or data.get("bankSlipUrl")

    if not provider_reference:
        raise PaymentCheckoutError("Asaas não retornou payment id.")

    return CheckoutSession(
        provider="asaas",
        provider_reference=provider_reference,
        checkout_url=checkout_url,
        expires_at=None,
        raw_payload={
            "customer": customer,
            "payment": data,
        },
    )


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
        return _create_manual_checkout(
            billing_request_id=billing_request_id,
            tenant_id=tenant_id,
            amount_cents=amount_cents,
            currency=currency,
            payment_method=payment_method,
            requested_plan_type=requested_plan_type,
        )

    if provider == "asaas":
        return _create_asaas_checkout(
            billing_request_id=billing_request_id,
            tenant_id=tenant_id,
            amount_cents=amount_cents,
            currency=currency,
            payment_method=payment_method,
            requested_plan_type=requested_plan_type,
        )

    raise PaymentCheckoutError(
        f"Provider de pagamento não suportado ainda: {provider}. "
        "Implemente o adaptador real antes de habilitar em produção."
    )
