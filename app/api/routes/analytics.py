"""HTTP-эндпоинты аналитики AutoCRM."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.database import get_session
from app.db.models.user import User
from app.schemas.analytics import (
    AnalyticsDashboardRead,
    ManagersRead,
    OverviewRead,
    SourcesRead,
    StageTimesRead,
)
from app.services.analytics import (
    AnalyticsPeriod,
    AnalyticsService,
    InvalidAnalyticsPeriod,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AnalyticsService:
    return AnalyticsService(session)


def get_period(
    date_from: Annotated[date, Query(description="Начало периода включительно")],
    date_to: Annotated[date, Query(description="Конец периода включительно")],
) -> AnalyticsPeriod:
    try:
        return AnalyticsPeriod.build(date_from, date_to)
    except InvalidAnalyticsPeriod as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/overview", response_model=OverviewRead)
async def get_overview(
    period: Annotated[AnalyticsPeriod, Depends(get_period)],
    service: Annotated[AnalyticsService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> OverviewRead:
    return await service.overview(period)


@router.get("/sources", response_model=SourcesRead)
async def get_sources(
    period: Annotated[AnalyticsPeriod, Depends(get_period)],
    service: Annotated[AnalyticsService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> SourcesRead:
    return await service.sources(period)


@router.get("/managers", response_model=ManagersRead)
async def get_managers(
    period: Annotated[AnalyticsPeriod, Depends(get_period)],
    service: Annotated[AnalyticsService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> ManagersRead:
    return await service.managers(period, limit)


@router.get("/stage-times", response_model=StageTimesRead)
async def get_stage_times(
    period: Annotated[AnalyticsPeriod, Depends(get_period)],
    service: Annotated[AnalyticsService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> StageTimesRead:
    return await service.stage_times(period)


@router.get("/dashboard", response_model=AnalyticsDashboardRead)
async def get_dashboard(
    period: Annotated[AnalyticsPeriod, Depends(get_period)],
    service: Annotated[AnalyticsService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
    manager_limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> AnalyticsDashboardRead:
    return await service.dashboard(period, manager_limit)
