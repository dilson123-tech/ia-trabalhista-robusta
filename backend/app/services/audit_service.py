from typing import Any, Optional
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    *,
    tenant_id: int,
    user_id: int,
    action: str,
    meta: Optional[dict[str, Any]] = None,
) -> None:
    """
    Registra uma ação auditável no sistema.

    - tenant_id: isolamento SaaS
    - user_id: quem executou
    - action: nome lógico da ação (ex: "case_created", "pdf_generated")
    - meta: dados adicionais (JSON)
    """

    audit = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        metadata=meta or {},
    )

    db.add(audit)
    db.commit()
