"""HTTP-эндпоинты аналитики AutoCRM."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.database import get_session
from app.core.user_profiles import profile_for
from app.db.enums import UserRole
from app.db.models.user import User
from app.schemas.analytics import (
    AnalyticsDashboardRead,
    ManagersRead,
    OverviewRead,
    SourcesRead,
    StageTimesRead,
)
from app.services.excel_export import build_xlsx
from app.services.analytics import (
    AnalyticsPeriod,
    AnalyticsService,
    InvalidAnalyticsPeriod,
)

router = APIRouter(prefix="/analytics", tags=["Аналитика"])


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Только для директора")
    return current_user


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
    _: Annotated[User, Depends(require_admin)],
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
    _: Annotated[User, Depends(require_admin)],
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
    _: Annotated[User, Depends(require_admin)],
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
    _: Annotated[User, Depends(require_admin)],
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
    _: Annotated[User, Depends(require_admin)],
    manager_limit: Annotated[
        int,
        Query(ge=1, le=100, description="Сколько менеджеров в блоке", examples=[10]),
    ] = 10,
) -> AnalyticsDashboardRead:
    return await service.dashboard(period, manager_limit)


@router.get("/export.xlsx")
async def export_dashboard_excel(
    period: Annotated[AnalyticsPeriod, Depends(get_period)],
    service: Annotated[AnalyticsService, Depends(get_service)],
    _: Annotated[User, Depends(require_admin)],
) -> Response:
    stats = await service.dashboard(period, 100)
    rows: list[list[object]] = []
    title_rows: set[int] = set()
    header_rows: set[int] = set()
    def title(text: str) -> None:
        rows.append([text]); title_rows.add(len(rows))
    def header(values: list[object]) -> None:
        rows.append(values); header_rows.add(len(rows))
    title("Отчёт AutoCRM")
    rows.append(["Период", f"{period.date_from.strftime('%d.%m.%Y')} — {period.date_to.strftime('%d.%m.%Y')}"])
    rows.append([]); title("Обзор"); header(["Показатель","Значение"])
    rows.extend([["Всего заявок",stats.overview.total_leads],["Продажи",stats.overview.sales],["Конверсия, %",stats.overview.conversion_percent],["Выручка",stats.overview.revenue],["Средний чек",stats.overview.average_check]])
    rows.append([]); title("Источники"); header(["Источник","Заявок","Доля, %"])
    source_labels={"telegram":"Telegram","manual":"Вручную","site":"Сайт"}
    for item in stats.sources.items: rows.append([source_labels.get(item.source.value,item.source.value),item.leads,item.share_percent])
    rows.append([]); title("Менеджеры"); header(["Фамилия и имя","Продажи","Выручка","Средний чек"])
    for item in stats.managers.items:
        user = await service.session.get(User, item.manager_id)
        name = profile_for(user.id,user.email,user.role.value).full_name if user else item.email
        rows.append([name,item.sales,item.revenue,item.revenue/item.sales if item.sales else 0])
    rows.append([]); title("Среднее время по этапам"); header(["Этап","Выборка","Среднее, минут","Медиана, минут"])
    status_labels={"new":"Новая","in_progress":"В работе","selection":"Подбор","invoice":"Счёт"}
    for item in stats.stage_times.items: rows.append([status_labels.get(item.stage.value,item.stage.value),item.sample_count,round(item.average_seconds/60),round(item.median_seconds/60)])
    content=build_xlsx(rows,sheet_name="Аналитика",title_rows=title_rows,header_rows=header_rows,widths=[28,20,20,20])
    return Response(content=content,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":"attachment; filename=autocrm-report.xlsx"})
