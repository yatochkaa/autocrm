"""Бизнес-логика позиций заказа."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

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
        self.repository = OrderItemRepository(session)

    async def _ensure_lead(self, lead_id: int) -> None:
        if not await self.repository.lead_exists(lead_id):
            raise OrderItemLeadNotFoundError

    async def add(self, lead_id: int, data: OrderItemCreate) -> OrderItem:
        await self._ensure_lead(lead_id)
        item = OrderItem(lead_id=lead_id, **data.model_dump())
        return await self.repository.save(item)

    async def list(self, lead_id: int) -> OrderItemsSummary:
        await self._ensure_lead(lead_id)
        items = [
            OrderItemRead.model_validate(item)
            for item in await self.repository.list(lead_id)
        ]
        return OrderItemsSummary.build(items)

    async def update(
        self,
        lead_id: int,
        item_id: int,
        data: OrderItemUpdate,
    ) -> OrderItem:
        await self._ensure_lead(lead_id)
        item = await self.repository.get(lead_id, item_id)
        if item is None:
            raise OrderItemNotFoundError

        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(item, field, value)
        return await self.repository.save(item)

    async def delete(self, lead_id: int, item_id: int) -> None:
        await self._ensure_lead(lead_id)
        item = await self.repository.get(lead_id, item_id)
        if item is None:
            raise OrderItemNotFoundError
        await self.repository.delete(item)
