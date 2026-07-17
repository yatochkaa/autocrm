"""Бизнес-логика заявок."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import LeadSource, LeadStatus
from app.db.models.audit_log import AuditLog
from app.db.models.lead import Lead
from app.db.models.order_item import OrderItem
from app.db.models.status_history import StatusHistory
from app.db.models.user import User
from app.domain.funnel import validate_transition
from app.domain.lead_data import LeadDataError, normalize_phone, resolve_vin
from app.repositories.lead import LeadRepository
from app.schemas.lead import LeadCreate, LeadUpdate


class LeadNotFoundError(LookupError):
    pass


class LeadService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = LeadRepository(session)

    @staticmethod
    def _set_totals(lead: Lead) -> None:
        lead.total_amount = round(
            sum((item.price or 0) * item.qty for item in lead.items), 2
        )
        margins = [
            (item.price - item.purchase_price) * item.qty
            for item in lead.items
            if item.price is not None and item.purchase_price is not None
        ]
        lead.total_margin = round(sum(margins), 2) if margins else None

    async def create(self, data: LeadCreate, current_user: User) -> Lead:
        lead = Lead(
            name=data.name,
            phone=normalize_phone(data.phone),
            source=data.source,
            vin=resolve_vin(data.vin, data.car_info, data.name),
            car_info=data.car_info,
            manager_id=data.manager_id or current_user.id,
            priority=data.priority.value,
            items=[OrderItem(**item.model_dump()) for item in data.items],
        )
        self._set_totals(lead)
        lead.audit_logs.append(
            AuditLog(actor_id=current_user.id, action="lead_created")
        )
        return await self.repository.save(lead)

    async def list(
        self,
        status: LeadStatus | None = None,
        source: LeadSource | None = None,
        manager_id: int | None = None,
    ) -> Sequence[Lead]:
        return await self.repository.list(status, source, manager_id)

    async def get(self, lead_id: int) -> Lead:
        lead = await self.repository.get(lead_id)
        if lead is None:
            raise LeadNotFoundError
        return lead

    async def update(self, lead_id: int, data: LeadUpdate, actor_id: int) -> Lead:
        lead = await self.get(lead_id)
        updates = data.model_dump(exclude_unset=True)

        if "phone" in updates:
            updates["phone"] = normalize_phone(updates["phone"])
        if "vin" in updates:
            value = updates["vin"]
            updates["vin"] = resolve_vin(value) if value else None
        if "priority" in updates and updates["priority"] is not None:
            updates["priority"] = updates["priority"].value

        changed_fields: list[str] = []
        for field, value in updates.items():
            if getattr(lead, field) != value:
                setattr(lead, field, value)
                changed_fields.append(field)

        if changed_fields:
            self.session.add(
                AuditLog(
                    lead_id=lead.id,
                    actor_id=actor_id,
                    action="lead_updated",
                    meta=",".join(changed_fields),
                )
            )
        return await self.repository.save(lead)

    async def change_status(
        self,
        lead_id: int,
        target: LeadStatus,
        current_user: User,
        rejection_reason: str | None = None,
    ) -> Lead:
        lead = await self.get(lead_id)
        previous = lead.status
        validate_transition(previous, target)
        if target == LeadStatus.LOST and not (rejection_reason or "").strip():
            raise LeadDataError("Для отказа необходимо указать причину")

        lead.status = target
        lead.rejection_reason = (
            rejection_reason.strip()
            if target == LeadStatus.LOST and rejection_reason
            else None
        )
        await self.repository.add_history(
            StatusHistory(
                lead_id=lead.id,
                from_status=previous.value,
                to_status=target.value,
                changed_by=current_user.id,
            )
        )
        self.session.add(
            AuditLog(
                lead_id=lead.id,
                actor_id=current_user.id,
                action="status_changed",
                field="status",
                old_value=previous.value,
                new_value=target.value,
            )
        )
        return await self.repository.save(lead)

    async def delete(self, lead_id: int) -> None:
        lead = await self.get(lead_id)
        await self.repository.delete(lead)
