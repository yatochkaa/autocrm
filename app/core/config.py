from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, читаются из ENV / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "AutoCRM API"
    debug: bool = False

    # Полный DSN можно задать напрямую через переменную DATABASE_URL.
    # Удобно для локального запуска на SQLite без Postgres/Docker.
    database_url_override: str | None = Field(
        default=None,
        validation_alias="DATABASE_URL",
    )

    # PostgreSQL (используется, если DATABASE_URL не задан)
    postgres_user: str = "autocrm"
    postgres_password: str = "autocrm"
    postgres_db: str = "autocrm"
    postgres_host: str = "db"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        """Async-DSN для SQLAlchemy. DATABASE_URL имеет приоритет."""
        if self.database_url_override:
            return self.database_url_override
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Кэшируем настройки, чтобы не читать .env на каждый вызов."""
    return Settings()


settings = get_settings()
