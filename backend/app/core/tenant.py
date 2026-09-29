from __future__ import annotations

from sqlalchemy import event, text
from sqlalchemy.orm import Session


_TENANT_INFO_KEY = "app_tenant_id"


@event.listens_for(Session, "after_begin")
def _reapply_tenant_after_begin(session: Session, transaction, connection) -> None:
    """
    Reaplica o tenant sempre que uma nova transação começa.

    O valor PostgreSQL é transaction-local, portanto não vaza pela conexão
    devolvida ao pool. A Session mantém apenas o tenant lógico em session.info.
    """
    tenant_id = session.info.get(_TENANT_INFO_KEY)
    if tenant_id is None:
        return

    if connection.dialect.name == "sqlite":
        return

    connection.execute(
        text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )


def set_tenant_on_session(db: Session, tenant_id: int) -> None:
    """
    Define o tenant lógico da Session.

    PostgreSQL:
    - guarda o tenant na própria Session;
    - usa set_config(..., true), limitado à transação atual;
    - após COMMIT/ROLLBACK, after_begin reaplica o mesmo tenant se a Session
      iniciar outra transação.

    SQLite:
    - mantém apenas session.info; não há RLS/GUC.
    """
    if isinstance(tenant_id, bool) or not isinstance(tenant_id, int) or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")

    db.info[_TENANT_INFO_KEY] = tenant_id

    dialect_name = db.get_bind().dialect.name
    if dialect_name == "sqlite":
        return

    db.execute(
        text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )


def clear_tenant_on_session(db: Session) -> None:
    """
    Remove o tenant lógico da Session e encerra a transação atual.

    Como app.tenant_id é transaction-local, encerrar a transação elimina
    também o contexto PostgreSQL sem deixar estado persistente no pool.
    """
    db.info.pop(_TENANT_INFO_KEY, None)

    try:
        if db.in_transaction():
            db.rollback()
    except Exception:
        # Helper de limpeza: não mascara a exceção original de uma rota.
        pass


def scoped_query(db: Session, model, current_user):
    """
    Retorna query já filtrada por tenant_id.
    """
    if isinstance(current_user, dict):
        tenant_id = current_user.get("tenant_id")
    else:
        tenant_id = current_user.tenant_id

    return db.query(model).filter(model.tenant_id == tenant_id)
