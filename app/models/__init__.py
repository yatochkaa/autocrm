# Импортируем модели здесь, чтобы Alembic видел их в Base.metadata.
from app.models.base import Base
from app.models.lead import Lead

__all__ = ["Base", "Lead"]
