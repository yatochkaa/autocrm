"""Модель заявки (Lead) — центральная сущность CRM."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import LeadSource, LeadStatus

if TYPE_CHECKING:
    from app.db.models.comment import Comment
    from app.db.models.order_item import OrderItem
    from app.db.models.status_history import StatusHistory
    from app.db.models.user import User


def _enum(enum_cls: type, length: int) -> Enum:
    """Enum, который хранится в БД как VARCHAR (переносимо между СУБД)."""
    return Enum(
        enum_cls,
        native_enum=False,
        length=length,
        values_callable=lambda e: [m.value for m in e],
    )


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), index=True)
    source: Mapped[LeadSource] = mapped_column(
        _enum(LeadSource, 20), default=LeadSource.MANUAL, nullable=False
    )
    vin: Mapped[str | None] = mapped_column(String(17), index=True)
    car_info: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[LeadStatus] = mapped_column(
        _enum(LeadStatus, 20), default=LeadStatus.NEW, index=True, nullable=False
    )
    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    manager: Mapped[User | None] = relationship(back_populates="leads")
    items: Mapped[list[OrderItem]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )
    history: Mapped[list[StatusHistory]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
        order_by="StatusHistory.changed_at",
    )
    comments: Mapped[list[Comment]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
        order_by="Comment.created_at",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Lead id={self.id} name={self.name!r} status={self.status}>"
