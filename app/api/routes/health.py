from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.core.config import settings
from app.core.database import get_session
from app.schemas.health import HealthStatus, ReadinessStatus
from app.services.health import HealthService

router = APIRouter(tags=["Система"])


@router.get(
    "/health",
    response_model=HealthStatus,
    summary="Проверка живости",
    description="Liveness-проба: приложение живо, внешние зависимости не проверяются.",
    responses={200: {"description": "Сервис работает"}},
)
async def health() -> HealthStatus:
    """Liveness: приложение живо, внешние зависимости не трогаем."""
    return HealthStatus(app=settings.app_name, version=__version__)


@router.get(
    "/health/db",
    response_model=ReadinessStatus,
    summary="Проверка БД",
    description="Readiness-проба: проверяет доступность базы данных.",
    responses={200: {"description": "Статус соединения с базой данных"}},
)
async def health_db(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReadinessStatus:
    """Readiness: проверяем соединение с БД."""
    db_ok = await HealthService(session).check_db()
    return ReadinessStatus(status="ok" if db_ok else "degraded", database=db_ok)
