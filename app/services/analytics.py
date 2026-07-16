"""Расчёты аналитики без AI: SQLAlchemy и обычный Python."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import LeadSource, LeadStatus
from app.repositories.analytics import AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsDashboardRead,
    AnalyticsPeriodRead,
    ManagerStatRead,
    ManagersRead,
    OverviewRead,
    SourceStatRead,
    SourcesRead,
    StageTimeRead,
    StageTimesRead,
)

BUSINESS_TIMEZONE = ZoneInfo("Europe/Moscow")

FUNNEL_STAGES = (
    LeadStatus.NEW,
    LeadStatus.IN_PROGRESS,
    LeadStatus.SELECTION,
    LeadStatus.INVOICE,
)


class InvalidAnalyticsPeriod(ValueError):
    pass


@dataclass(frozen=True)
class AnalyticsPeriod:
    date_from: date
    date_to: date
    start: datetime
    end_exclusive: datetime

    @classmethod
    def build(cls, date_from: date, date_to: date) -> "AnalyticsPeriod":
        if date_from > date_to:
            raise InvalidAnalyticsPeriod("date_from не может быть позже date_to")
        local_start = datetime.combine(
            date_from,
            time.min,
            tzinfo=BUSINESS_TIMEZONE,
        )
        local_end_exclusive = datetime.combine(
            date_to + timedelta(days=1),
            time.min,
            tzinfo=BUSINESS_TIMEZONE,
        )
        return cls(
            date_from=date_from,
            date_to=date_to,
            start=local_start.astimezone(timezone.utc),
            end_exclusive=local_end_exclusive.astimezone(timezone.utc),
        )

    def read(self) -> AnalyticsPeriodRead:
        return AnalyticsPeriodRead(date_from=self.date_from, date_to=self.date_to)


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = AnalyticsRepository(session)

    async def overview(self, period: AnalyticsPeriod) -> OverviewRead:
        total_leads, sales, revenue = await self.repository.overview(
            period.start,
            period.end_exclusive,
        )
        conversion = (sales / total_leads * 100) if total_leads else 0
        average_check = (revenue / sales) if sales else 0
        return OverviewRead(
            period=period.read(),
            total_leads=total_leads,
            sales=sales,
            conversion_percent=round(conversion, 2),
            revenue=round(revenue, 2),
            average_check=round(average_check, 2),
        )

    async def sources(self, period: AnalyticsPeriod) -> SourcesRead:
        rows = dict(
            await self.repository.sources(period.start, period.end_exclusive)
        )
        total = sum(rows.values())
        items = [
            SourceStatRead(
                source=source,
                leads=rows.get(source, 0),
                share_percent=round(rows.get(source, 0) / total * 100, 2)
                if total
                else 0,
            )
            for source in LeadSource
        ]
        return SourcesRead(
            period=period.read(),
            items=items,
            labels=[item.source.value for item in items],
            values=[item.leads for item in items],
        )

    async def managers(
        self,
        period: AnalyticsPeriod,
        limit: int,
    ) -> ManagersRead:
        rows = await self.repository.managers(
            period.start,
            period.end_exclusive,
            limit,
        )
        items = [
            ManagerStatRead(
                manager_id=manager_id,
                email=email,
                sales=sales,
                revenue=round(revenue, 2),
            )
            for manager_id, email, sales, revenue in rows
        ]
        return ManagersRead(
            period=period.read(),
            items=items,
            labels=[item.email for item in items],
            sales_values=[item.sales for item in items],
            revenue_values=[item.revenue for item in items],
        )

    async def stage_times(self, period: AnalyticsPeriod) -> StageTimesRead:
        rows = await self.repository.stage_history(
            period.start,
            period.end_exclusive,
        )
        durations: dict[LeadStatus, list[float]] = defaultdict(list)
        current_lead_id: int | None = None
        entered_at: datetime | None = None

        for lead_id, lead_created_at, from_status, _, changed_at in rows:
            if lead_id != current_lead_id:
                current_lead_id = lead_id
                entered_at = lead_created_at
            if entered_at is None or from_status is None:
                entered_at = changed_at
                continue
            try:
                stage = LeadStatus(from_status)
            except ValueError:
                entered_at = changed_at
                continue
            seconds = max((changed_at - entered_at).total_seconds(), 0)
            if stage in FUNNEL_STAGES:
                durations[stage].append(seconds)
            entered_at = changed_at

        items = []
        for stage in FUNNEL_STAGES:
            samples = durations.get(stage, [])
            average_seconds = sum(samples) / len(samples) if samples else 0
            items.append(
                StageTimeRead(
                    stage=stage,
                    sample_count=len(samples),
                    average_seconds=round(average_seconds, 2),
                    average_hours=round(average_seconds / 3600, 2),
                )
            )
        return StageTimesRead(
            period=period.read(),
            items=items,
            labels=[item.stage.value for item in items],
            values_hours=[item.average_hours for item in items],
        )

    async def dashboard(
        self,
        period: AnalyticsPeriod,
        manager_limit: int,
    ) -> AnalyticsDashboardRead:
        return AnalyticsDashboardRead(
            overview=await self.overview(period),
            sources=await self.sources(period),
            managers=await self.managers(period, manager_limit),
            stage_times=await self.stage_times(period),
        )
