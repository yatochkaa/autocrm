# PartsPrice Hub — этап 2: модели данных и первая миграция

Этот архив содержит **только новые файлы** этапа 2. Распакуй и скопируй папки
в корень проекта `PartsPrice` (с заменой одноимённых файлов). Ничего из этапа 0
не удаляется.

## Куда что класть

```
app/db/base.py               <- базовый класс моделей
app/db/session.py            <- движок + фабрика сессий (sync)
app/db/enums.py              <- перечисления (роли, источники, статусы)
app/db/models/__init__.py    <- регистрация всех моделей
app/db/models/user.py
app/db/models/lead.py
app/db/models/order_item.py
app/db/models/status_history.py
app/db/models/comment.py
app/schemas/__init__.py      <- Pydantic-схемы (create/read/update)
app/schemas/user.py
app/schemas/lead.py
app/schemas/order_item.py
app/schemas/status_history.py
app/schemas/comment.py
alembic.ini                  <- если у тебя его ещё нет
alembic/env.py               <- заменить сгенерированный env.py
alembic/script.py.mako       <- если его ещё нет
alembic/versions/0001_initial_schema.py
scripts/check_models.py      <- мини-проверка
tests/test_models.py         <- pytest-тесты
```

## Зависимости (добавь в requirements.txt, если ещё нет)

```
SQLAlchemy>=2.0.31
alembic>=1.13
pydantic>=2.7
psycopg[binary]>=3.1   # драйвер PostgreSQL для sync-подключения
```

Для локального SQLite драйвер не нужен (встроен в Python).

## Быстрая проверка (без Postgres и без Docker)

```
python -m scripts.check_models
```
Ожидаемо: `OK: модели и связи этапа 2 работают корректно`

Или через pytest:
```
pytest -q
```
Ожидаемо: `2 passed`

## Применить миграцию к реальной БД

Локально на SQLite:
```
set DATABASE_URL=sqlite:///./partsprice.db
alembic upgrade head
```

В PostgreSQL (Docker) строка вида:
```
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/partsprice
alembic upgrade head
```

Один и тот же код и миграция работают в обеих БД.
