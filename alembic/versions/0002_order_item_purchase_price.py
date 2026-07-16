"""add purchase price to order items

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-17
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "order_items",
        sa.Column("purchase_price", sa.Numeric(12, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("order_items", "purchase_price")
