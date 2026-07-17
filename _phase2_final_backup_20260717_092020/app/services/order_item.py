"""Бизнес-логика позиций заказа с синхронизацией итогов заявки."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.lead import Lead
from app.db.models.order_item import OrderItem
from app.repositories.order_item import OrderItemRepository
from app.schemas.order_item import (
    OrderItemCreate,
    OrderItemRead,
    OrderItemsSummary,
    OrderItemUpdate,
)


class OrderItemLeadNotFoundError(LookupError):
    pass


class OrderItemNotFoundError(LookupError):
    pass


class OrderItemService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = OrderItemRepository(session)

    async def _ensure_lead(self, lead_id: int) -> None:
        if not await self.repository.lead_exists(lead_id):
            raise OrderItemLeadNotFoundError

    async def _sync_totals(self, lead_id: int) -> None:
        values = await self.session.execute(
            select(
                func.coalesce(
                    func.sum(OrderItem.qty * func.coalesce(OrderItem.price, 0)), 0
                ),
                func.sum(OrderItem.qty * (OrderItem.price - OrderItem.purchase_price)),
            ).where(OrderItem.lead_id == lead_id)
        )
        total_amount, total_margin = values.one()
        lead = await self.session.get(Lead, lead_id)
        if lead is not None:
            lead.total_amount = float(total_amount or 0)
            lead.total_margin = (
                float(total_margin) if total_margin is not None else None
            )
            await self.session.commit()

    async def add(self, lead_id: int, data: OrderItemCreate) -> OrderItem:
        await self._ensure_lead(lead_id)
        item = await self.repository.save(
            OrderItem(lead_id=lead_id, **data.model_dump())
        )
        await self._sync_totals(lead_id)
        return item

    async def list(self, lead_id: int) -> OrderItemsSummary:
        await self._ensure_lead(lead_id)
        items = [
            OrderItemRead.model_validate(item)
            for item in await self.repository.list(lead_id)
        ]
        return OrderItemsSummary.build(items)

    async def update(
        self, lead_id: int, item_id: int, data: OrderItemUpdate
    ) -> OrderItem:
        await self._ensure_lead(lead_id)
        item = await self.repository.get(lead_id, item_id)
        if item is None:
            raise OrderItemNotFoundError
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        item = await self.repository.save(item)
        await self._sync_totals(lead_id)
        return item

    async def delete(self, lead_id: int, item_id: int) -> None:
        await self._ensure_lead(lead_id)
        item = await self.repository.get(lead_id, item_id)
        if item is None:
            raise OrderItemNotFoundError
        await self.repository.delete(item)
        await self._sync_totals(lead_id)
