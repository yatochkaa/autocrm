# PartsPrice Hub — тест этапа 2 на Docker (PostgreSQL)

Цель: проверить, что модели и миграция этапа 2 работают на настоящем PostgreSQL, а не только на SQLite.

## Файлы

- `docker-compose.yml` — в корень проекта.
- `scripts/check_db.py` — рядом с `scripts/check_models.py`.
- `.env.docker.example` — образец строки подключения.

## Шаги (Windows, из корня PartsPrice с активным venv)

```
:: 1) Поднять PostgreSQL в контейнере
docker compose up -d

:: 2) Проверить, что база готова (STATUS = healthy)
docker compose ps

:: 3) Драйвер PostgreSQL для Python (если ещё не стоит)
pip install "psycopg[binary]"

:: 4) Указать строку подключения к Postgres в Docker
set DATABASE_URL=postgresql+psycopg://partsprice:partsprice@localhost:5432/partsprice

:: 5) Применить миграцию (создаёт 5 таблиц)
alembic upgrade head

:: 6) Проверить модели на реальной БД
python -m scripts.check_db
```

Ожидаемый вывод шага 6:
```
Подключение: postgresql+psycopg://partsprice:***@localhost:5432/partsprice
Заявок в БД: 1; позиций у первой: 1
OK: подключение к реальной БД и модели работают
```

## Посмотреть таблицы глазами

```
docker compose exec db psql -U partsprice -d partsprice -c "\dt"
```
Должно быть 5 таблиц: users, leads, order_items, status_history, comments (+ alembic_version).

## Остановить / очистить

```
docker compose down        :: остановить (данные остаются в томе pgdata)
docker compose down -v      :: остановить и стереть базу
```

Важное: код моделей и миграция одинаковы для SQLite и PostgreSQL — меняется только DATABASE_URL.
