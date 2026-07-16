"""Конфигурация Alembic (синхронный режим)."""
from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

# Импортируем метаданные всех моделей.
from app.db.base import Base
import app.db.models  # noqa: F401  регистрирует все таблицы в Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_url() -> str:
    try:
        from app.core.config import get_settings

        settings = get_settings()
        for attr in ("DATABASE_URL", "database_url"):
            value = getattr(settings, attr, None)
            if value:
                return str(value)
    except Exception:
        pass
    return os.getenv("DATABASE_URL", "sqlite:///./partsprice.db")


def run_migrations_offline() -> None:
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_get_url(), poolclass=pool.NullPool, future=True)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,  # нужно для ALTER в SQLite
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
