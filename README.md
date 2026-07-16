# AutoCRM — Backend (этап 0: каркас)

CRM для магазина автозапчастей. Этот репозиторий содержит базовый каркас backend.

## Стек

Python 3.12 · FastAPI · async SQLAlchemy 2.0 · Alembic (async) · PostgreSQL · pydantic-settings · Docker · ruff + black · pytest.

## Быстрый старт

```bash
# 1. Локально (venv)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env

# 2. Поднять всё в Docker
docker compose up --build           # API: http://localhost:8000 , docs: /docs

# 3. Первая миграция (когда появятся модели)
docker compose exec api alembic revision --autogenerate -m "init"
docker compose exec api alembic upgrade head

# 4. Линт и тесты
ruff check . && black --check .
pytest
```

## Проверка

- `GET /health` → `{"status":"ok","app":"AutoCRM API","version":"0.1.0"}` (не трогает БД)
- `GET /health/db` → `{"status":"ok","database":true}` (проверяет соединение с PostgreSQL)

## Слои

- **api/** — HTTP-маршруты и валидация.
- **core/** — конфиг, подключение к БД, инфраструктура.
- **domain/** — доменные типы и правила (например, стадии воронки).
- **models/** — ORM-модели SQLAlchemy.
- **schemas/** — Pydantic-схемы (DTO) для API.
- **repositories/** — доступ к данным (CRUD).
- **services/** — бизнес-логика.
