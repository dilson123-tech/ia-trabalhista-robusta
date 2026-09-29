"""enable tenant RLS policies

Revision ID: b7e2d4c1f905
Revises: a4b9c6d7e810
Create Date: 2026-09-27 00:00:00.000000

ENABLE + FORCE ROW LEVEL SECURITY com policy FOR ALL (USING + WITH CHECK) nas
tabelas tenant-scoped. Fail-closed: sem app.tenant_id definido, nenhuma linha é
visível nem gravável. Acesso administrativo apenas por membership na role
NOLOGIN ia_rls_admin (sem BYPASSRLS); a policy funciona mesmo se essa role não
existir (o EXISTS simplesmente retorna falso). Não cria roles nem altera schema.
tenants e users ficam fora do RLS.
"""

from __future__ import annotations

from alembic import op


revision = "b7e2d4c1f905"
down_revision = "a4b9c6d7e810"
branch_labels = None
depends_on = None


POLICY_NAME = "tenant_isolation"

RLS_TABLES = (
    "usage_counters",
    "subscriptions",
    "cases",
    "audit_logs",
    "case_party_states",
    "case_parties",
    "case_party_representatives",
    "case_party_relationships",
    "case_party_events",
    "case_timeline_items",
    "business_audit_logs",
    "case_attachments",
    "tenant_usage_events",
    "tenant_members",
    "editable_documents",
    "editable_document_versions",
    "case_evidence_checklist_items",
    "case_analyses",
    "billing_requests",
    "appeal_reaction_states",
    "appeal_decision_points",
    "appeal_deadlines",
    "appeal_strategy_items",
    "appeal_draft_refs",
    "case_contact_logs",
)

_TENANT_MATCH = (
    "(pg_catalog.current_setting('app.tenant_id', true) ~ '^[1-9][0-9]*$' "
    "AND tenant_id::text = pg_catalog.current_setting('app.tenant_id', true))"
)

_IS_RLS_ADMIN = (
    "EXISTS (SELECT 1 FROM pg_catalog.pg_roles r "
    "WHERE r.rolname = 'ia_rls_admin' "
    "AND pg_catalog.pg_has_role(current_user, r.oid, 'MEMBER'))"
)

_POLICY_EXPR = f"({_TENANT_MATCH}) OR {_IS_RLS_ADMIN}"


def upgrade() -> None:
    for table in RLS_TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
        op.execute(
            f'CREATE POLICY "{POLICY_NAME}" ON "{table}" '
            f"AS PERMISSIVE FOR ALL "
            f"USING ({_POLICY_EXPR}) "
            f"WITH CHECK ({_POLICY_EXPR})"
        )


def downgrade() -> None:
    for table in reversed(RLS_TABLES):
        op.execute(f'DROP POLICY IF EXISTS "{POLICY_NAME}" ON "{table}"')
        op.execute(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
