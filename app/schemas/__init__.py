"""Pydantic-схемы (DTO) для валидации входных данных и сериализации ответов."""

from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate
from app.schemas.lead import LeadCreate, LeadRead, LeadUpdate
from app.schemas.order_item import (
    OrderItemCreate,
    OrderItemRead,
    OrderItemUpdate,
)
from app.schemas.status_history import (
    StatusHistoryCreate,
    StatusHistoryRead,
)
from app.schemas.user import UserCreate, UserRead, UserUpdate

__all__ = [
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "LeadCreate",
    "LeadRead",
    "LeadUpdate",
    "OrderItemCreate",
    "OrderItemRead",
    "OrderItemUpdate",
    "StatusHistoryCreate",
    "StatusHistoryRead",
    "CommentCreate",
    "CommentRead",
    "CommentUpdate",
]
