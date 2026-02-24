from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session


def validate_subscription(db: Session, tenant_id: int):
    sub = db.execute(
        text("""
            SELECT plan_type, case_limit, active, expires_at
            FROM subscriptions
            WHERE tenant_id = :tid
        """),
        {"tid": tenant_id},
    ).fetchone()

    if not sub:
        raise HTTPException(status_code=403, detail="subscription not found")

    plan_type, case_limit, active, expires_at = sub

    if not active:
        raise HTTPException(status_code=403, detail="subscription inactive")

    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="subscription expired")

    return case_limit


def enforce_case_limit(db: Session, tenant_id: int, case_limit: int):
    count = db.execute(
        text("SELECT COUNT(*) FROM cases WHERE tenant_id = :tid"),
        {"tid": tenant_id},
    ).scalar()

    if count >= case_limit:
        raise HTTPException(
            status_code=403,
            detail="case limit reached for current plan",
        )
