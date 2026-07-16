# AutoCRM — этап 3: JWT-авторизация и роли

Архив содержит только новые и изменённые файлы этапа 3.

## Куда копировать

Распакуй архив отдельно и скопируй содержимое в корень `autocrm2` с заменой:

- `app/core/security.py` — новый;
- `app/core/config.py` — заменить;
- `app/repositories/user.py` — новый;
- `app/services/auth.py` — новый;
- `app/schemas/auth.py` — новый;
- `app/api/dependencies/__init__.py` — новый;
- `app/api/dependencies/auth.py` — новый;
- `app/api/routes/auth.py` — новый;
- `app/api/router.py` — заменить;
- `scripts/create_admin.py` — новый;
- `tests/conftest.py` — заменить;
- `tests/test_auth.py` — новый;
- `requirements.txt` — заменить;
- `.env.stage3.example` — подсказка; значения добавь в `.env`.

Новая миграция не нужна: `users`, `password_hash` и `role` уже есть в миграции `0001`.

## Как встроено в слои

- `api/routes/auth.py` — HTTP;
- `api/dependencies/auth.py` — Bearer JWT и роли;
- `schemas/auth.py` — DTO;
- `services/auth.py` — регистрация/логин;
- `repositories/user.py` — async-запросы к users;
- `core/security.py` — bcrypt и JWT;
- `db/models/user.py` — существующая модель.

API использует существующую `AsyncSession` из `app/core/database.py`. Синхронная `app/db/session.py` остаётся для Alembic и служебного скрипта создания admin.

## Установка и тесты (cmd, команды по одной)

```bat
pip install -r requirements-dev.txt
set DATABASE_URL=postgresql+psycopg://partsprice:partsprice@localhost:5432/partsprice
pytest tests/test_auth.py -q
```

Ожидаемо: `4 passed`.

## Запуск и Swagger

```bat
uvicorn app.main:app --reload
```

Открой `http://127.0.0.1:8000/docs`.

1. `POST /auth/register`:
```json
{"email": "manager@example.com", "password": "strongpass123"}
```
2. `POST /auth/login` — скопируй `access_token`.
3. Нажми **Authorize**, вставь только токен.
4. `GET /auth/me` вернёт пользователя.
5. После **Logout** `/auth/me` вернёт `401`.

## Первый admin

Публичная регистрация всегда создаёт manager — иначе любой мог бы назначить себя admin.

```bat
python -m scripts.create_admin
```

## Защита будущего endpoint

```python
from typing import Annotated
from fastapi import Depends
from app.api.dependencies.auth import require_role
from app.db.enums import UserRole
from app.db.models.user import User

@router.get("/admin-only")
async def admin_only(
    user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
):
    return {"email": user.email}
```
