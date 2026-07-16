from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class HealthService:
    """Бизнес-логика проверок работоспособности."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def check_db(self) -> bool:
        """True, если БД отвечает на тривиальный запрос."""
        result = await self._session.execute(text("SELECT 1"))
        return result.scalar_one() == 1
