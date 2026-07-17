# 🚗 AutoCRM — CRM для магазина автозапчастей

[![CI](https://github.com/yatochkaa/autocrm/actions/workflows/ci.yml/badge.svg)](https://github.com/yatochkaa/autocrm/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)
![pytest](https://img.shields.io/badge/tested_with-pytest-0A9EDC?logo=pytest&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)

CRM-система для магазина автозапчастей: заявки клиентов (источники —
Telegram / сайт / вручную) ведутся менеджером по воронке продаж, по каждой
заявке подбираются запчасти (оригиналы и аналоги), считаются **сумма и
маржа**, а аналитика выводится на **дашборд**.

**Воронка:** `Новая → В работе → Подбор → Счёт → Продажа / Отказ`

🔗 **Live demo:** https://autocrm-demo.up.railway.app · **Swagger:** https://autocrm-demo.up.railway.app/docs

> Демо-доступ: `manager@autocrm.local` / `manager123`

---

## 📸 Скриншоты

<!-- TODO: добавить реальные скриншоты/GIF в docs/screenshots/ -->

| Воронка (kanban) | Карточка заявки | Дашборд |
|---|---|---|
| ![Kanban](docs/screenshots/kanban.png) | ![Lead](docs/screenshots/lead.png) | ![Dashboard](docs/screenshots/dashboard.png) |

---

## ✨ Возможности

- 🧭 Kanban-воронка заявок с drag-and-drop (@dnd-kit) и историей смены статусов
- 🔧 Позиции подбора: OEM-номера, бренды, оригинал/аналог, цена и закупка
- 💰 Авторасчёт: `line_total = price × qty`, `line_margin = (price − purchase_price) × qty`
- 📊 Аналитика: продажи, источники, менеджеры, конверсия по этапам (Recharts)
- 🔐 JWT-авторизация, роли admin/manager, приоритеты и причины отказа
- 📝 Комментарии к заявкам и полный audit log действий
- 🧪 CI: ruff + проверка миграций + pytest на каждый push

## 🛠 Стек

| Слой | Технологии |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| БД | PostgreSQL 16 (asyncpg / psycopg3) |
| Auth | JWT (PyJWT), passlib + bcrypt |
| Frontend | React 18, TypeScript, Vite, React Router, Recharts, @dnd-kit |
| Инфраструктура | Docker, docker-compose (db + api + frontend), GitHub Actions |
| Тесты | pytest (async), ruff |

---

## 🚀 Quickstart

Нужны только Docker и docker compose:

```bash
git clone https://github.com/yatochkaa/autocrm.git
cd autocrm
cp .env.example .env

docker compose up --build
```

После запуска:

| Сервис | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |

Наполнить базу демо-данными:

```bash
# пользователи (admin + manager) и несколько демо-заявок
docker compose exec api python -m app.seed

# ~60 реалистичных заявок с историей статусов для дашборда
docker compose exec api python -m scripts.seed_portfolio --count 60
```

Логин: `manager@autocrm.local` / `manager123` (переопределяется через `SEED_*` в `.env`).

Тесты (локально, нужен запущенный PostgreSQL — см. `.github/workflows/ci.yml`):

```bash
pip install -r requirements-dev.txt
pytest -q
```

---

## 🏗 Architecture

Слоистая архитектура — каждый слой знает только о слое ниже:

```mermaid
flowchart TD
    subgraph Clients
        UI[React SPA]
        EXT[Заявки: Telegram / сайт / вручную]
    end

    subgraph Backend[FastAPI Backend — пакет app/]
        API[api — роутеры: auth, leads, order_items, analytics, comments]
        SCH[schemas — Pydantic-модели входа/выхода]
        SRV[services — бизнес-логика: воронка, маржа, аналитика]
        DOM[domain — сущности и правила предметной области]
        REPO[repositories — доступ к данным]
        MOD[db — Base, enums, ORM-модели SQLAlchemy]
        CORE[core — config, database, security/JWT]
    end

    DB[(PostgreSQL)]

    UI --> API
    EXT --> API
    API --> SCH
    API --> SRV
    SRV --> DOM
    SRV --> REPO
    REPO --> MOD
    MOD --> DB
    CORE -.-> API
    CORE -.-> REPO
```

### Структура проекта

```
autocrm/
├── app/
│   ├── api/            # роутеры FastAPI + зависимости
│   ├── core/           # конфиг, подключение к БД, JWT/security
│   ├── db/             # Base, enums, ORM-модели
│   ├── domain/         # доменные сущности и правила
│   ├── repositories/   # доступ к данным
│   ├── schemas/        # Pydantic-схемы
│   ├── services/       # бизнес-логика
│   ├── main.py         # фабрика приложения
│   └── seed.py         # сид: пользователи + демо-заявки
├── alembic/            # миграции БД
├── frontend/           # React + TypeScript + Vite
├── scripts/            # seed_portfolio.py и утилиты
├── tests/              # pytest
├── docker-compose.yml  # db + api + frontend
└── Dockerfile          # образ API
```

### Схема БД

```mermaid
erDiagram
    USERS ||--o{ LEADS : "manages"
    LEADS ||--o{ ORDER_ITEMS : "contains"
    LEADS ||--o{ STATUS_HISTORY : "logs"
    LEADS ||--o{ AUDIT_LOGS : "tracks"
    LEADS ||--o{ COMMENTS : "has"

    USERS {
        int id PK
        string email UK
        string password_hash
        string role "admin | manager"
    }

    LEADS {
        int id PK
        string name "имя клиента"
        string phone
        string source "telegram | site | manual"
        string vin
        string car_info
        string status "new | in_progress | selection | invoice | won | lost"
        int manager_id FK
        string priority "low | normal | high | urgent"
        string rejection_reason "nullable"
        float total_amount "сумма продажи"
        float total_margin "маржа"
        datetime created_at
        datetime updated_at
    }

    ORDER_ITEMS {
        int id PK
        int lead_id FK
        string oem "OEM-номер"
        string brand
        string name
        float price "цена продажи"
        float purchase_price "закупка"
        int qty
        bool is_analog
    }

    STATUS_HISTORY {
        int id PK
        int lead_id FK
        string from_status
        string to_status
        int changed_by FK
        datetime changed_at
    }

    AUDIT_LOGS {
        int id PK
        int lead_id FK
        int actor_id FK
        string action
        string field
        string old_value
        string new_value
        datetime created_at
    }

    COMMENTS {
        int id PK
        int lead_id FK
        int author_id FK
        string text
        datetime created_at
    }
```

### Путь заявки (sequence)

```mermaid
sequenceDiagram
    actor C as Клиент
    participant SRC as Источник (Telegram / сайт / менеджер)
    participant A as FastAPI (api)
    participant S as LeadService (services)
    participant R as LeadRepository (repositories)
    participant DB as PostgreSQL
    participant F as React SPA

    C->>SRC: "Нужны колодки на Camry 2019"
    SRC->>A: POST /leads (source, phone, vin, car_info)
    A->>A: JWT + валидация (schemas)
    A->>S: create_lead(dto)
    S->>R: add(lead)
    R->>DB: INSERT leads + status_history + audit_log
    DB-->>A: 201 Created

    F->>A: GET /leads?status=new
    A-->>F: заявка на kanban-доске
    Note over F: Менеджер двигает заявку по воронке,<br/>добавляет позиции — сумма и маржа считаются автоматически

    F->>A: GET /analytics/*
    A-->>F: дашборд: продажи, источники, конверсия
```

---

## 🌐 Деплой

Проект разворачивается на [Railway](https://railway.app) (PostgreSQL + API + frontend).
Пошаговая инструкция: [docs/DEPLOY.md](docs/DEPLOY.md).

## 🗺 Roadmap

- [x] Воронка заявок с kanban и историей статусов
- [x] Позиции подбора (оригинал/аналог) с расчётом суммы и маржи
- [x] JWT-авторизация, роли admin/manager
- [x] Аналитика и дашборд
- [x] Комментарии и audit log
- [x] CI (ruff + миграции + pytest)
- [ ] Telegram-бот для автоматического приёма заявок
- [ ] Экспорт отчётов в Excel/CSV
- [ ] Интеграция с поставщиками (проценка по API)
- [ ] Уведомления менеджеру о новых заявках

## 📄 Лицензия

MIT
