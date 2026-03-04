import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.user import User
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.api.v1.routes.auth import login, LoginIn, pwd_context


def test_login_blocked_if_user_inactive():
    """
    Usuário existe, senha correta, mas is_active = False
    → login deve levantar HTTP 403 (user is inactive).
    """

    # Banco isolado em memória só para este teste
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    # Criar tenant (apenas com campos que realmente existem no modelo)
    tenant = Tenant(name="Test Tenant")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    # Criar usuário INATIVO com senha hash compatível
    u = User(
        username="inactive_user",
        password_hash=pwd_context.hash("dev"),
        role="admin",
        is_active=False,
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    # Criar membership para não cair no "no tenant membership"
    membership = TenantMember(user_id=u.id, tenant_id=tenant.id)
    db.add(membership)
    db.commit()

    # Montar payload igual do endpoint
    payload = LoginIn(username="inactive_user", password="dev")

    # Chamar a função de login diretamente
    with pytest.raises(HTTPException) as excinfo:
        login(payload, db=db)

    err = excinfo.value
    assert err.status_code == 403
    assert "inactive" in err.detail
