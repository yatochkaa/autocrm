from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Базовый репозиторий: общие операции доступа к данным."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, obj_id: int) -> ModelT | None:
        """Вернуть объект по первичному ключу или None."""
        return await self.session.get(self.model, obj_id)

    async def list(self) -> Sequence[ModelT]:
        """Вернуть все объекты."""
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def add(self, obj: ModelT) -> ModelT:
        """Добавить объект в сессию и выполнить flush (чтобы получить id)."""
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete(self, obj: ModelT) -> None:
        """Удалить объект."""
        await self.session.delete(obj)
        await self.session.flush()
