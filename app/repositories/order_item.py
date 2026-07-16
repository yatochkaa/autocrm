"""Запросы к позициям заказа."""
from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.lead import Lead
from app.db.models.order_item import OrderItem


class OrderItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def lead_exists(self, lead_id: int) -> bool:
        return await self.session.scalar(select(Lead.id).where(Lead.id == lead_id)) is not None

    async def get(self, lead_id: int, item_id: int) -> OrderItem | None:
        statement = select(OrderItem).where(
            OrderItem.id == item_id,
            OrderItem.lead_id == lead_id,
        )
        return await self.session.scalar(statement)

    async def list(self, lead_id: int) -> Sequence[OrderItem]:
        statement = (
            select(OrderItem)
            .where(OrderItem.lead_id == lead_id)
            .order_by(OrderItem.id)
        )
        result = await self.session.scalars(statement)
        return result.all()

    async def save(self, item: OrderItem) -> OrderItem:
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete(self, item: OrderItem) -> None:
        await self.session.delete(item)
        await self.session.commit()
