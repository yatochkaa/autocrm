"""Базовый декларативный класс для всех ORM-моделей."""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Единые правила именования индексов/ключей -> предсказуемые имена в миграциях.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Общий базовый класс: от него наследуются все модели."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
