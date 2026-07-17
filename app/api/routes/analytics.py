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

router = APIRouter(prefix="/analytics", tags=["Аналитика"])


def get_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AnalyticsService:
    return AnalyticsService(session)


def get_period(
    date_from: Annotated[
        date,
        Query(
            description="Начало периода включительно (YYYY-MM-DD)",
            examples=["2026-01-01"],
        ),
    ],
    date_to: Annotated[
        date,
        Query(
            description="Конец периода включительно (YYYY-MM-DD)",
            examples=["2026-01-31"],
        ),
    ],
) -> AnalyticsPeriod:
    try:
        return AnalyticsPeriod.build(date_from, date_to)
    except InvalidAnalyticsPeriod as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


ANALYTICS_RESPONSES = {
    200: {"description": "Данные аналитики за период"},
    401: {"description": "Не авторизован — требуется валидный токен"},
    422: {"description": "Некорректный период (например, date_from > date_to)"},
}


@router.get(
    "/overview",
    response_model=OverviewRead,
    summary="Обзор продаж",
    description=(
        "Ключевые метрики за период: количество заявок, продажи, "
        "конверсия, выручка и средний чек."
    ),
    responses=ANALYTICS_RESPONSES,
)
async def get_overview(
    period: Annotated[AnalyticsPeriod, Depends(get_period)],
    service: Annotated[AnalyticsService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> OverviewRead:
    return await service.overview(period)


@router.get(
    "/sources",
    response_model=SourcesRead,
    summary="Заявки по источникам",
    description="Распределение заявок по источникам за период (для графиков).",
    responses=ANALYTICS_RESPONSES,
)
async def get_sources(
    period: Annotated[AnalyticsPeriod, Depends(get_period)],
    service: Annotated[AnalyticsService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> SourcesRead:
    return await service.sources(period)


@router.get(
    "/managers",
    response_model=ManagersRead,
    summary="Топ менеджеров",
    description="Рейтинг менеджеров по продажам и выручке за период.",
    responses=ANALYTICS_RESPONSES,
)
async def get_managers(
    period: Annotated[AnalyticsPeriod, Depends(get_period)],
    service: Annotated[AnalyticsService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Сколько менеджеров вернуть", examples=[10]),
    ] = 10,
) -> ManagersRead:
    return await service.managers(period, limit)


@router.get(
    "/stage-times",
    response_model=StageTimesRead,
    summary="Среднее время на этапах",
    description="Среднее время нахождения заявок на каждом этапе воронки.",
    responses=ANALYTICS_RESPONSES,
)
async def get_stage_times(
    period: Annotated[AnalyticsPeriod, Depends(get_period)],
    service: Annotated[AnalyticsService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> StageTimesRead:
    return await service.stage_times(period)


@router.get(
    "/dashboard",
    response_model=AnalyticsDashboardRead,
    summary="Сводный дашборд",
    description=(
        "Собирает обзор, источники, менеджеров и время на этапах "
        "в один ответ для дашборда."
    ),
    responses=ANALYTICS_RESPONSES,
)
async def get_dashboard(
    period: Annotated[AnalyticsPeriod, Depends(get_period)],
    service: Annotated[AnalyticsService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
    manager_limit: Annotated[
        int,
        Query(ge=1, le=100, description="Сколько менеджеров в блоке", examples=[10]),
    ] = 10,
) -> AnalyticsDashboardRead:
    return await service.dashboard(period, manager_limit)
