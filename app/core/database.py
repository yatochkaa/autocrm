from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


@lru_cache
def get_engine() -> AsyncEngine:
    """Лениво создаём async-движок (один на приложение).

    Ленивость важна: импорт приложения не должен тянуть драйвер БД,
    пока база реально не нужна (например, тест /health).
    """
    return create_async_engine(settings.database_url, echo=settings.debug, future=True)


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Фабрика сессий; expire_on_commit=False — объекты доступны после commit."""
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI-зависимость: выдаёт async-сессию и закрывает её."""
    async with get_session_factory()() as session:
        yield session
