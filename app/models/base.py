from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Общий Declarative Base для всех ORM-моделей."""


class TimestampMixin:
    """Добавляет столбцы created_at / updated_at."""

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
