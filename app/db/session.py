"""Синхронный движок SQLAlchemy и фабрика сессий.

Синхронный драйвер выбран намеренно: проще в установке
(PostgreSQL через psycopg, SQLite «из коробки») и не требует сборки asyncpg.
Строка подключения берётся из настроек проекта или из переменной окружения
DATABASE_URL.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_URL = "sqlite:///./partsprice.db"


def _database_url() -> str:
    """Достаёт DATABASE_URL из настроек проекта или из окружения."""
    try:
        from app.core.config import get_settings

        settings = get_settings()
        for attr in ("DATABASE_URL", "database_url"):
            value = getattr(settings, attr, None)
            if value:
                return str(value)
    except Exception:
        # На раннем этапе настроек может не быть — не падаем.
        pass
    return os.getenv("DATABASE_URL", DEFAULT_URL)


engine = create_engine(_database_url(), pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False, class_=Session
)


def get_session() -> Iterator[Session]:
    """FastAPI-зависимость: отдаёт сессию и гарантированно её закрывает."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
