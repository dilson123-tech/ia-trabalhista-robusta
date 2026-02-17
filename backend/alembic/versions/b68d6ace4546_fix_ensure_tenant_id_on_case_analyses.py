"""fix: ensure tenant_id on case_analyses"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b68d6ace4546'
down_revision = '91463a3e1b0c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # verifica se coluna já existe
    result = conn.execute(sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='case_analyses'
        AND column_name='tenant_id'
    """))
    exists = result.fetchone()

    if not exists:
        op.add_column(
            "case_analyses",
            sa.Column("tenant_id", sa.Integer(), nullable=True),
        )

        op.execute("UPDATE case_analyses SET tenant_id = 1 WHERE tenant_id IS NULL")

        op.alter_column("case_analyses", "tenant_id", nullable=False)

        op.create_foreign_key(
            "fk_case_analyses_tenant_id",
            "case_analyses",
            "tenants",
            ["tenant_id"],
            ["id"],
            ondelete="CASCADE",
        )

        op.create_index(
            "ix_case_analyses_tenant_id",
            "case_analyses",
            ["tenant_id"],
        )


def downgrade() -> None:
    pass
