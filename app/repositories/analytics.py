"""SQLAlchemy-запросы для аналитики."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import LeadStatus
from app.db.models.lead import Lead
from app.db.models.order_item import OrderItem
from app.db.models.status_history import StatusHistory
from app.db.models.user import User


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _period_filter(date_from: datetime, date_to_exclusive: datetime):
        return (
            Lead.created_at >= date_from,
            Lead.created_at < date_to_exclusive,
        )

    async def overview(
        self,
        date_from: datetime,
        date_to_exclusive: datetime,
    ) -> tuple[int, int, float]:
        period_filter = self._period_filter(date_from, date_to_exclusive)
        total_leads = await self.session.scalar(
            select(func.count(Lead.id)).where(*period_filter)
        )
        sales = await self.session.scalar(
            select(func.count(Lead.id)).where(
                *period_filter,
                Lead.status == LeadStatus.WON,
            )
        )
        revenue_value = await self.session.scalar(
            select(func.coalesce(func.sum(OrderItem.price * OrderItem.qty), 0))
            .select_from(Lead)
            .join(OrderItem, OrderItem.lead_id == Lead.id, isouter=True)
            .where(
                *period_filter,
                Lead.status == LeadStatus.WON,
            )
        )
        revenue = float(revenue_value or Decimal("0"))
        return int(total_leads or 0), int(sales or 0), revenue

    async def sources(
        self,
        date_from: datetime,
        date_to_exclusive: datetime,
    ) -> list[tuple[object, int]]:
        statement = (
            select(Lead.source, func.count(Lead.id))
            .where(*self._period_filter(date_from, date_to_exclusive))
            .group_by(Lead.source)
        )
        rows = (await self.session.execute(statement)).all()
        return [(source, int(count)) for source, count in rows]

    async def managers(
        self,
        date_from: datetime,
        date_to_exclusive: datetime,
        limit: int,
    ) -> list[tuple[int, str, int, float]]:
        sales_count = func.count(distinct(Lead.id))
        revenue_sum = func.coalesce(func.sum(OrderItem.price * OrderItem.qty), 0)
        statement = (
            select(User.id, User.email, sales_count, revenue_sum)
            .select_from(User)
            .join(Lead, Lead.manager_id == User.id)
            .join(OrderItem, OrderItem.lead_id == Lead.id, isouter=True)
            .where(
                *self._period_filter(date_from, date_to_exclusive),
                Lead.status == LeadStatus.WON,
            )
            .group_by(User.id, User.email)
            .order_by(sales_count.desc(), revenue_sum.desc(), User.id)
            .limit(limit)
        )
        rows = (await self.session.execute(statement)).all()
        return [
            (int(manager_id), email, int(sales), float(revenue or 0))
            for manager_id, email, sales, revenue in rows
        ]

    async def stage_history(
        self,
        date_from: datetime,
        date_to_exclusive: datetime,
    ) -> list[tuple[int, datetime, str | None, str, datetime]]:
        statement = (
            select(
                Lead.id,
                Lead.created_at,
                StatusHistory.from_status,
                StatusHistory.to_status,
                StatusHistory.changed_at,
            )
            .join(StatusHistory, StatusHistory.lead_id == Lead.id)
            .where(*self._period_filter(date_from, date_to_exclusive))
            .order_by(Lead.id, StatusHistory.changed_at, StatusHistory.id)
        )
        return list((await self.session.execute(statement)).all())
