"""История смены статусов заявки (аудит движения по воронке)."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.lead import Lead
    from app.db.models.user import User


class StatusHistory(Base):
    __tablename__ = "status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), index=True, nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    lead: Mapped["Lead"] = relationship(back_populates="history")
    changed_by_user: Mapped["User | None"] = relationship(
        back_populates="status_changes"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<StatusHistory id={self.id} lead_id={self.lead_id} "
            f"{self.from_status}->{self.to_status}>"
        )
