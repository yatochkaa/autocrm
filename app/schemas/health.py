from pydantic import BaseModel


class HealthStatus(BaseModel):
    """Ответ liveness-проверки."""

    status: str = "ok"
    app: str
    version: str


class ReadinessStatus(BaseModel):
    """Ответ readiness-проверки (доступность БД)."""

    status: str
    database: bool
