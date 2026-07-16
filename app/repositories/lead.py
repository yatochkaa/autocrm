from collections.abc import Sequence

from sqlalchemy import select

from app.domain.enums import LeadStatus
from app.models.lead import Lead
from app.repositories.base import BaseRepository


class LeadRepository(BaseRepository[Lead]):
    """Доступ к заявкам в БД."""

    model = Lead

    async def list_leads(self, status: LeadStatus | None = None) -> Sequence[Lead]:
        """Список заявок (новые сверху), опционально фильтр по статусу."""
        stmt = select(Lead).order_by(Lead.created_at.desc())
        if status is not None:
            stmt = stmt.where(Lead.status == status)
        result = await self.session.execute(stmt)
        return result.scalars().all()
