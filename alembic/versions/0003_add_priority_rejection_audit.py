"""add priority, rejection_reason, audit_log; updated_at for comments; recalculate totals

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-17
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing_tables = set(insp.get_table_names())

    def cols(table: str) -> set:
        return {c["name"] for c in insp.get_columns(table)}

    def idxs(table: str) -> set:
        return {i["name"] for i in insp.get_indexes(table)}

    # ── 1. leads: новые поля ─────────────────────────────────────────────
    lead_cols = cols("leads")

    if "priority" not in lead_cols:
        op.add_column("leads",
            sa.Column("priority", sa.String(20), nullable=False, server_default="normal"))

    if "rejection_reason" not in lead_cols:
        op.add_column("leads",
            sa.Column("rejection_reason", sa.Text, nullable=True))

    if "total_amount" not in lead_cols:
        op.add_column("leads",
            sa.Column("total_amount", sa.Float, nullable=False, server_default="0"))

    if "total_margin" not in lead_cols:
        op.add_column("leads",
            sa.Column("total_margin", sa.Float, nullable=True))

    lead_ix = idxs("leads")
    if "ix_leads_priority" not in lead_ix:
        op.create_index("ix_leads_priority", "leads", ["priority"])

    # ── 2. Пересчитать total_amount / total_margin из order_items ──────────────
    # Читаем поля после добавления, чтобы пересчитать для существующих заявок
    if "order_items" in existing_tables:
        conn.execute(sa.text("""
            UPDATE leads
            SET
                total_amount = COALESCE((
                    SELECT SUM(COALESCE(qty,1) * COALESCE(price, 0))
                    FROM order_items
                    WHERE order_items.lead_id = leads.id
                ), 0),
                total_margin = (
                    SELECT SUM(CASE
                        WHEN price IS NOT NULL AND purchase_price IS NOT NULL
                        THEN COALESCE(qty,1) * (price - purchase_price)
                        ELSE NULL
                    END)
                    FROM order_items
                    WHERE order_items.lead_id = leads.id
                )
        """))

    # ── 3. comments: updated_at ───────────────────────────────────────────────────
    if "comments" in existing_tables:
        comment_cols = cols("comments")
        if "updated_at" not in comment_cols:
            op.add_column("comments",
                sa.Column(
                    "updated_at",
                    sa.DateTime(timezone=True),
                    server_default=sa.text("now()"),
                    nullable=False,
                ))

    # ── 4. audit_log (новая таблица) ────────────────────────────────────────────
    if "audit_log" not in existing_tables:
        op.create_table(
            "audit_log",
            sa.Column("id",         sa.Integer,  primary_key=True),
            sa.Column("lead_id",    sa.Integer,
                sa.ForeignKey("leads.id", ondelete="SET NULL"), nullable=True),
            sa.Column("actor_id",   sa.Integer,
                sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("action",     sa.String(100), nullable=False),
            sa.Column("field",      sa.String(100), nullable=True),
            sa.Column("old_value",  sa.Text, nullable=True),
            sa.Column("new_value",  sa.Text, nullable=True),
            sa.Column("meta",       sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True),
                server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("ix_audit_log_lead_id",    "audit_log", ["lead_id"])
        op.create_index("ix_audit_log_actor_id",   "audit_log", ["actor_id"])
        op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if "comments" in insp.get_table_names():
        comment_cols = {c["name"] for c in insp.get_columns("comments")}
        if "updated_at" in comment_cols:
            op.drop_column("comments", "updated_at")
    op.drop_table("audit_log")
    op.drop_index("ix_leads_priority", table_name="leads")
    op.drop_column("leads", "total_margin")
    op.drop_column("leads", "total_amount")
    op.drop_column("leads", "rejection_reason")
    op.drop_column("leads", "priority")
