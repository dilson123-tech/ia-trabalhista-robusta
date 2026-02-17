"""feat(d07): case analyses table (CI-safe)

Revision ID: a8232a6b8077
Revises: 954b29d19d99
Create Date: 2026-02-14 10:24:44
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "a8232a6b8077"
down_revision = "954b29d19d99"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    # Fresh DB (CI): cria tudo do zero, bonitinho
    if not insp.has_table("case_analyses"):
        op.create_table(
            "case_analyses",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "case_id",
                sa.Integer(),
                sa.ForeignKey("cases.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("analysis", sa.JSON(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )
        op.create_index("ix_case_analyses_case_id", "case_analyses", ["case_id"], unique=False)
        op.create_index(
            "ix_case_analyses_case_id_created_at",
            "case_analyses",
            ["case_id", "created_at"],
            unique=False,
        )
        return

    # DB existente (dev): nunca tenta ADD NOT NULL direto (quebra com dados antigos)
    cols = {c["name"] for c in insp.get_columns("case_analyses")}

    if "analysis" not in cols:
        op.add_column("case_analyses", sa.Column("analysis", sa.JSON(), nullable=True))

    # garante sem NULL antes de travar NOT NULL
    op.execute("UPDATE case_analyses SET analysis = '{}'::json WHERE analysis IS NULL")
    op.alter_column("case_analyses", "analysis", nullable=False)

    if "created_at" not in cols:
        op.add_column(
            "case_analyses",
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    idx = {i.get("name") for i in insp.get_indexes("case_analyses")}
    if "ix_case_analyses_case_id" not in idx:
        op.create_index("ix_case_analyses_case_id", "case_analyses", ["case_id"], unique=False)
    if "ix_case_analyses_case_id_created_at" not in idx:
        op.create_index(
            "ix_case_analyses_case_id_created_at",
            "case_analyses",
            ["case_id", "created_at"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("case_analyses"):
        return

    idx = {i.get("name") for i in insp.get_indexes("case_analyses")}
    if "ix_case_analyses_case_id_created_at" in idx:
        op.drop_index("ix_case_analyses_case_id_created_at", table_name="case_analyses")
    if "ix_case_analyses_case_id" in idx:
        op.drop_index("ix_case_analyses_case_id", table_name="case_analyses")

    op.drop_table("case_analyses")
