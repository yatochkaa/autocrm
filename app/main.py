from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.router import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Хуки старта/остановки (прогрев кэшей, пулы и т.п.)."""
    yield


def create_app() -> FastAPI:
    """Фабрика приложения — удобно для тестов и разных конфигураций."""
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.include_router(api_router)
    return app


app = create_app()
