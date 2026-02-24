import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.db.session import get_db
from app.models.user import User
from app.models.tenant_member import TenantMember
from app.core.security import issue_token

client = TestClient(app)


def test_cross_tenant_isolation(db_session):
    # 1️⃣ Criar usuário
    user = User(
        username="isolado@test.com",
        password_hash="fakehash",
        role="advogado",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 2️⃣ Garantir membership no tenant 1
    membership = TenantMember(
        tenant_id=1,
        user_id=user.id,
        role="advogado",
    )
    db_session.add(membership)
    db_session.commit()

    # 3️⃣ Emitir token válido
    token = issue_token(user.username, "advogado", tenant_id=1)

    headers = {"Authorization": f"Bearer {token}"}

    # 4️⃣ Deve acessar normalmente (endpoint de exemplo protegido)
    resp_ok = client.get("/cases", headers=headers)
    assert resp_ok.status_code in (200, 404)  # pode não haver cases ainda

    # 5️⃣ Remover membership (simula outro tenant)
    db_session.delete(membership)
    db_session.commit()

    resp_blocked = client.get("/cases", headers=headers)

    # 🔒 Não pode vazar existência → 404
    assert resp_blocked.status_code == 404
