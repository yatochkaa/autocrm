# Деплой AutoCRM на Railway

Схема: PostgreSQL + API (Dockerfile в корне) + frontend (frontend/Dockerfile, nginx).

## 1. База данных

1. [railway.app](https://railway.app) → New Project → **Deploy PostgreSQL**.
2. Railway создаст сервис Postgres с переменной `DATABASE_URL`.

## 2. Backend (API)

1. В том же проекте: **New Service → GitHub Repo** → `yatochkaa/autocrm`.
2. `railway.json` в корне подхватится автоматически (Dockerfile + миграции на старте).
3. Variables:
   - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`, но с заменой префикса:
     Railway выдаёт `postgresql://...` — нужно `postgresql+psycopg://...`
     (psycopg3 работает и для alembic, и для async-приложения).
     Проще всего задать вручную:
     `postgresql+psycopg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.RAILWAY_PRIVATE_DOMAIN}}:5432/${{Postgres.PGDATABASE}}`
   - `SECRET_KEY` — сгенерировать: `openssl rand -hex 32`
   - `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`, `SEED_MANAGER_EMAIL`, `SEED_MANAGER_PASSWORD` —
     креды для демо-входа (не используй личный email).
4. Один раз наполнить демо-данными (Service → Shell или `railway run`):

   ```bash
   python -m app.seed
   python -m scripts.seed_portfolio --count 60
   ```

5. Settings → Networking → **Generate Domain** → Swagger будет по пути `/docs`,
   healthcheck — `/health`.

## 3. Frontend

**Вариант A — Railway (рекомендуется):**

1. **New Service → GitHub Repo** → тот же репозиторий.
2. Settings → Build: **Root Directory = `frontend`** (соберётся `frontend/Dockerfile`).
3. Variables: `API_UPSTREAM=https://<домен-api>.up.railway.app`
   (nginx проксирует `/api/*` на этот адрес, CORS не нужен).
4. Generate Domain → это и есть публичное демо.

**Вариант B — Vercel/Netlify:** деплой папки `frontend/`, но тогда нужен rewrite
`/api/* → https://<домен-api>/*` (например, через `vercel.json`), потому что
SPA ходит на относительный путь `/api`.

## 4. Проверка

- `https://<api>/health` отвечает, `https://<api>/docs` открывается;
- логин через `POST /auth/login` с кредами из `SEED_*`;
- фронтенд показывает kanban с демо-заявками и дашборд с аналитикой;
- после деплоя обнови ссылки Live demo в README.md.
