"""Модель пользователя системы (менеджер / администратор)."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import UserRole

if TYPE_CHECKING:
    from app.db.models.comment import Comment
    from app.db.models.lead import Lead
    from app.db.models.status_history import StatusHistory


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            native_enum=False,
            length=20,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=UserRole.MANAGER,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Заявки, где пользователь — ответственный менеджер.
    leads: Mapped[list["Lead"]] = relationship(back_populates="manager")
    # Комментарии, написанные пользователем.
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")
    # Записи истории смены статусов, сделанные пользователем.
    status_changes: Mapped[list["StatusHistory"]] = relationship(
        back_populates="changed_by_user"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
