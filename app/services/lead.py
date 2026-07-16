from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import LeadStatus
from app.domain.funnel import FunnelError, InvalidTransition, can_transition
from app.models.lead import Lead
from app.repositories.lead import LeadRepository
from app.schemas.lead import LeadCreate, LeadUpdate


class LeadService:
    """Бизнес-логика заявок и движения по воронке."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LeadRepository(session)

    async def create(self, data: LeadCreate) -> Lead:
        """Создать заявку (стартовый статус NEW из дефолта модели)."""
        lead = Lead(**data.model_dump())
        await self._repo.add(lead)
        await self._session.commit()
        await self._session.refresh(lead)
        return lead

    async def get(self, lead_id: int) -> Lead | None:
        return await self._repo.get(lead_id)

    async def list(self, status: LeadStatus | None = None) -> Sequence[Lead]:
        return await self._repo.list_leads(status)

    async def update(self, lead_id: int, data: LeadUpdate) -> Lead | None:
        """Частично обновить поля заявки (кроме статуса)."""
        lead = await self._repo.get(lead_id)
        if lead is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(lead, field, value)
        await self._session.commit()
        await self._session.refresh(lead)
        return lead

    async def change_status(self, lead_id: int, target: LeadStatus) -> Lead | None:
        """Перевести заявку на следующую стадию с проверкой правил воронки."""
        lead = await self._repo.get(lead_id)
        if lead is None:
            return None
        if not can_transition(lead.status, target):
            raise InvalidTransition(lead.status, target)
        if target == LeadStatus.WON and lead.sale_amount is None:
            raise FunnelError(
                "Нельзя перевести в 'Продажа' без суммы продажи (sale_amount)."
            )
        lead.status = target
        await self._session.commit()
        await self._session.refresh(lead)
        return lead

    async def delete(self, lead_id: int) -> bool:
        """Удалить заявку. True — удалена, False — не найдена."""
        lead = await self._repo.get(lead_id)
        if lead is None:
            return False
        await self._repo.delete(lead)
        await self._session.commit()
        return True
