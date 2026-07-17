"""Пакет моделей.

Импортируем все модели здесь, чтобы Base.metadata знал обо всех таблицах
(это нужно Alembic для autogenerate и create_all).
"""

from app.db.base import Base
from app.db.models.audit_log import AuditLog as AuditLog
from app.db.models.comment import Comment as Comment
from app.db.models.lead import Lead
from app.db.models.order_item import OrderItem
from app.db.models.status_history import StatusHistory
from app.db.models.user import User

__all__ = [
    "Base",
    "User",
    "Lead",
    "OrderItem",
    "StatusHistory",
    "Comment" "AuditLog",
]
