"""Запросы к таблицам leads и status_history."""
from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.enums import LeadSource, LeadStatus
from app.db.models.lead import Lead
from app.db.models.status_history import StatusHistory


class LeadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _with_relations(self):
        return (selectinload(Lead.items), selectinload(Lead.history))

    async def get(self, lead_id: int) -> Lead | None:
        statement = (
            select(Lead)
            .options(*self._with_relations())
            .where(Lead.id == lead_id)
            # Обновляет уже загруженный Lead и его relations в identity map.
            .execution_options(populate_existing=True)
        )
        return await self.session.scalar(statement)

    async def list(
        self,
        status: LeadStatus | None = None,
        source: LeadSource | None = None,
        manager_id: int | None = None,
    ) -> Sequence[Lead]:
        statement = select(Lead).options(*self._with_relations())
        if status is not None:
            statement = statement.where(Lead.status == status)
        if source is not None:
            statement = statement.where(Lead.source == source)
        if manager_id is not None:
            statement = statement.where(Lead.manager_id == manager_id)
        statement = statement.order_by(Lead.created_at.desc(), Lead.id.desc())
        result = await self.session.scalars(statement)
        return result.all()

    async def save(self, lead: Lead) -> Lead:
        self.session.add(lead)
        await self.session.commit()
        return await self.get(lead.id)  # type: ignore[return-value]

    async def add_history(self, history: StatusHistory) -> None:
        self.session.add(history)

    async def delete(self, lead: Lead) -> None:
        await self.session.delete(lead)
        await self.session.commit()
