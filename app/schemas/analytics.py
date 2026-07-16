"""Схемы ответов аналитики AutoCRM."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.db.enums import LeadSource, LeadStatus


class AnalyticsPeriodRead(BaseModel):
    date_from: date
    date_to: date


class OverviewRead(BaseModel):
    period: AnalyticsPeriodRead
    total_leads: int
    sales: int
    conversion_percent: float
    revenue: float
    average_check: float


class SourceStatRead(BaseModel):
    source: LeadSource
    leads: int
    share_percent: float


class SourcesRead(BaseModel):
    period: AnalyticsPeriodRead
    items: list[SourceStatRead]
    labels: list[str]
    values: list[int]


class ManagerStatRead(BaseModel):
    manager_id: int
    email: str
    sales: int
    revenue: float


class ManagersRead(BaseModel):
    period: AnalyticsPeriodRead
    items: list[ManagerStatRead]
    labels: list[str]
    sales_values: list[int]
    revenue_values: list[float]


class StageTimeRead(BaseModel):
    stage: LeadStatus
    sample_count: int
    average_seconds: float
    average_hours: float


class StageTimesRead(BaseModel):
    period: AnalyticsPeriodRead
    items: list[StageTimeRead]
    labels: list[str]
    values_hours: list[float]


class AnalyticsDashboardRead(BaseModel):
    overview: OverviewRead
    sources: SourcesRead
    managers: ManagersRead
    stage_times: StageTimesRead
