"""initial schema: users, leads, order_items, status_history, comments

Revision ID: 0001
Revises:
Create Date: 2026-07-16
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), server_default="manager", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("source", sa.String(length=20), server_default="manual", nullable=False),
        sa.Column("vin", sa.String(length=17), nullable=True),
        sa.Column("car_info", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="new", nullable=False),
        sa.Column("manager_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["manager_id"], ["users.id"], name="fk_leads_manager_id_users", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_leads"),
    )
    op.create_index("ix_leads_phone", "leads", ["phone"])
    op.create_index("ix_leads_vin", "leads", ["vin"])
    op.create_index("ix_leads_status", "leads", ["status"])
    op.create_index("ix_leads_manager_id", "leads", ["manager_id"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("oem", sa.String(length=100), nullable=True),
        sa.Column("brand", sa.String(length=100), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("qty", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_analog", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.ForeignKeyConstraint(
            ["lead_id"], ["leads.id"], name="fk_order_items_lead_id_leads", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_order_items"),
    )
    op.create_index("ix_order_items_lead_id", "order_items", ["lead_id"])
    op.create_index("ix_order_items_oem", "order_items", ["oem"])

    op.create_table(
        "status_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(length=30), nullable=True),
        sa.Column("to_status", sa.String(length=30), nullable=False),
        sa.Column("changed_by", sa.Integer(), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"], ["leads.id"], name="fk_status_history_lead_id_leads", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["changed_by"], ["users.id"], name="fk_status_history_changed_by_users", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_status_history"),
    )
    op.create_index("ix_status_history_lead_id", "status_history", ["lead_id"])
    op.create_index("ix_status_history_changed_by", "status_history", ["changed_by"])

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"], ["leads.id"], name="fk_comments_lead_id_leads", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["author_id"], ["users.id"], name="fk_comments_author_id_users", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_comments"),
    )
    op.create_index("ix_comments_lead_id", "comments", ["lead_id"])
    op.create_index("ix_comments_author_id", "comments", ["author_id"])


def downgrade() -> None:
    op.drop_table("comments")
    op.drop_table("status_history")
    op.drop_table("order_items")
    op.drop_table("leads")
    op.drop_table("users")
