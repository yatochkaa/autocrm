"""Позиция подбора запчастей внутри заявки."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.lead import Lead


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), index=True, nullable=False
    )
    oem: Mapped[str | None] = mapped_column(String(100), index=True)
    brand: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[float | None] = mapped_column(Numeric(12, 2, asdecimal=False))
    purchase_price: Mapped[float | None] = mapped_column(
        Numeric(12, 2, asdecimal=False)
    )
    qty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_analog: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    lead: Mapped[Lead] = relationship(back_populates="items")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OrderItem id={self.id} name={self.name!r} qty={self.qty}>"
