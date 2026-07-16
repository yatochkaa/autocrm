"""create leads table

Revision ID: 0001_create_leads
Revises:
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_create_leads"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

# Enum как VARCHAR + CHECK (native_enum=False) — совпадает с моделью.
lead_source = sa.Enum(
    "telegram", "manual", "website", name="leadsource", native_enum=False
)
lead_status = sa.Enum(
    "new", "in_progress", "selection", "invoice", "won", "lost",
    name="leadstatus", native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_name", sa.String(length=200), nullable=False),
        sa.Column("contact", sa.String(length=200), nullable=True),
        sa.Column("part_query", sa.Text(), nullable=False),
        sa.Column("source", lead_source, nullable=False),
        sa.Column("status", lead_status, nullable=False),
        sa.Column("sale_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("cost_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_leads_status", "leads", ["status"])


def downgrade() -> None:
    op.drop_index("ix_leads_status", table_name="leads")
    op.drop_table("leads")
