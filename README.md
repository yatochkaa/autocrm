# AutoCRM — Backend (этап 0: каркас)

[![CI](https://github.com/yatochkaa/autocrm/actions/workflows/ci.yml/badge.svg)](https://github.com/yatochkaa/autocrm/actions/workflows/ci.yml)

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

# 3. Применить миграции
docker compose exec api alembic upgrade head

# 4. Линт и тесты
ruff check app tests
pytest -q
```

## Проверка

- `GET /health` → `{"status":"ok","app":"AutoCRM API","version":"0.1.0"}`.
- `GET /health/db` → `{"status":"ok","database":true}`.
- GitHub Actions поднимает PostgreSQL 16 и запускает `ruff`, миграции и `pytest` на каждый push и pull request.

## Слои

- **api/** — HTTP-маршруты и валидация.
- **core/** — конфиг, подключение к БД, инфраструктура.
- **domain/** — доменные типы и правила.
- **db/models/** — актуальные ORM-модели SQLAlchemy.
- **schemas/** — Pydantic-схемы API.
- **repositories/** — доступ к данным.
- **services/** — бизнес-логика.
