from sqlalchemy import text
from sqlalchemy.orm import Session


def set_tenant_on_session(db: Session, tenant_id: int) -> None:
    # SQLite (tests): não existe set_config / RLS vars. No-op.
    dialect_name = db.get_bind().dialect.name
    if dialect_name == "sqlite":
        return

    """
    Define tenant_id na conexão ativa para RLS funcionar.
    """
    db.execute(
        text("SELECT set_config('app.tenant_id', :tenant_id, false)"),
        {"tenant_id": str(tenant_id)},
    )


def scoped_query(db: Session, model, current_user):
    """
    Retorna query já filtrada por tenant_id.
    """
    if isinstance(current_user, dict):
        tenant_id = current_user.get("tenant_id")
    else:
        tenant_id = current_user.tenant_id

    return db.query(model).filter(model.tenant_id == tenant_id)
