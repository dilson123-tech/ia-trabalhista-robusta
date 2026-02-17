from sqlalchemy.orm import Session
from typing import Type

def scoped_query(db: Session, model: Type, claims: dict):
    """
    Query já filtrada por tenant automaticamente.
    Evita vazamento cross-tenant por erro humano.
    """
    return db.query(model).filter(
        model.tenant_id == claims["tenant_id"]
    )
