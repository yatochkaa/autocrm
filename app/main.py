"""Точка входа FastAPI-приложения AutoCRM."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.router import api_router
from app.core.config import settings

API_DESCRIPTION = """
**AutoCRM API** — сервис для управления заявками магазина автозапчастей:
клиенты, позиции заказа (оригиналы и аналоги) и аналитика продаж.

## Как авторизоваться

1. Выполните `POST /auth/login`, передав ваш `email` и `password`.
2. Скопируйте значение `access_token` из ответа.
3. Нажмите кнопку **Authorize** в правом верхнем углу.
4. Вставьте **только токен**, без слова `Bearer`.

После этого все защищённые запросы будут выполняться от вашего имени.

## Расчёты по позициям заказа

- `line_total = price × qty` — стоимость позиции.
- `line_margin = (price − purchase_price) × qty` — маржа позиции.
"""

TAGS_METADATA = [
    {
        "name": "Авторизация",
        "description": "Регистрация, вход и получение JWT-токена.",
    },
    {
        "name": "Заявки",
        "description": "Создание, просмотр, обновление и смена статуса заявок.",
    },
    {
        "name": "Позиции заказа",
        "description": "Позиции (оригиналы и аналоги) заявки и расчёт итогов.",
    },
    {
        "name": "Аналитика",
        "description": "Отчёты по продажам, источникам, менеджерам и этапам.",
    },
    {
        "name": "Система",
        "description": "Служебные проверки состояния сервиса.",
    },
]

SWAGGER_UI_PARAMETERS = {
    "persistAuthorization": True,
    "displayRequestDuration": True,
    "filter": True,
    "docExpansion": "none",
    "operationsSorter": "method",
}


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
        description=API_DESCRIPTION,
        openapi_tags=TAGS_METADATA,
        swagger_ui_parameters=SWAGGER_UI_PARAMETERS,
    )
    app.include_router(api_router)
    return app


app = create_app()
