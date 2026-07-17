"""Development seed for AutoCRM.

Run from the project root:
    python -m app.seed

The seed is idempotent: users and demo leads are matched by email/phone and
are not duplicated on repeated runs.
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select

from app.core.database import get_engine, get_session_factory
from app.core.security import hash_password
from app.db.enums import LeadSource, LeadStatus, UserRole
from app.db.models import Lead, OrderItem, StatusHistory, User

ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "volgarec999@mail.ru").strip().lower()
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "qwerty123")
MANAGER_EMAIL = os.getenv("SEED_MANAGER_EMAIL", "manager@autocrm.local").strip().lower()
MANAGER_PASSWORD = os.getenv("SEED_MANAGER_PASSWORD", "Manager123!")

DEMO_LEADS: list[dict[str, Any]] = [
    {
        "name": "Алексей Морозов",
        "phone": "+79990001001",
        "source": LeadSource.TELEGRAM,
        "vin": "XTA210990Y2765432",
        "car_info": "Lada Vesta 2020",
        "status": LeadStatus.NEW,
        "days_ago": 0,
        "items": [
            ("Фильтр масляный", "21080-1012005", "LADA", 2, 650, 410, False),
        ],
    },
    {
        "name": "Марина Крылова",
        "phone": "+79990001002",
        "source": LeadSource.SITE,
        "vin": "Z94CB41AAGR323456",
        "car_info": "Kia Rio 2017",
        "status": LeadStatus.NEW,
        "days_ago": 1,
        "items": [
            ("Колодки передние", "58101-H5A25", "Mando", 1, 5400, 3900, False),
        ],
    },
    {
        "name": "Дмитрий Соколов",
        "phone": "+79990001003",
        "source": LeadSource.MANUAL,
        "vin": "Z94K241CBLR123456",
        "car_info": "Hyundai Solaris 2020",
        "status": LeadStatus.NEW,
        "days_ago": 2,
        "items": [],
    },
    {
        "name": "Ольга Белова",
        "phone": "+79990001004",
        "source": LeadSource.TELEGRAM,
        "vin": "XW7BF4FK90S123456",
        "car_info": "Toyota Camry 2019",
        "status": LeadStatus.IN_PROGRESS,
        "days_ago": 3,
        "items": [
            ("Стойка стабилизатора", "48820-33070", "Toyota", 2, 4300, 3100, False),
        ],
    },
    {
        "name": "Сергей Павлов",
        "phone": "+79990001005",
        "source": LeadSource.SITE,
        "vin": "XW8ZZZ61ZKG123456",
        "car_info": "Volkswagen Polo 2019",
        "status": LeadStatus.IN_PROGRESS,
        "days_ago": 4,
        "items": [
            ("Свеча зажигания", "04E905612C", "NGK", 4, 1450, 920, True),
        ],
    },
    {
        "name": "Анна Волкова",
        "phone": "+79990001006",
        "source": LeadSource.MANUAL,
        "vin": "X7LLSRB1H5H123456",
        "car_info": "Renault Logan 2017",
        "status": LeadStatus.IN_PROGRESS,
        "days_ago": 5,
        "items": [],
    },
    {
        "name": "Иван Кузнецов",
        "phone": "+79990001007",
        "source": LeadSource.TELEGRAM,
        "vin": "TMBJG7NE7H0123456",
        "car_info": "Skoda Octavia 2017",
        "status": LeadStatus.SELECTION,
        "days_ago": 6,
        "items": [
            ("Комплект ГРМ", "04E198119", "INA", 1, 18900, 13900, True),
            ("Помпа", "04E121600", "HEPU", 1, 8200, 6100, True),
        ],
    },
    {
        "name": "Елена Фролова",
        "phone": "+79990001008",
        "source": LeadSource.SITE,
        "vin": "X9F4XXEED4AB12345",
        "car_info": "Ford Focus 2014",
        "status": LeadStatus.SELECTION,
        "days_ago": 7,
        "items": [
            ("Амортизатор передний", "1709762", "Sachs", 2, 9800, 7200, True),
        ],
    },
    {
        "name": "Николай Власов",
        "phone": "+79990001009",
        "source": LeadSource.MANUAL,
        "vin": "XTA219010K0123456",
        "car_info": "Lada Granta 2019",
        "status": LeadStatus.SELECTION,
        "days_ago": 8,
        "items": [
            ("Диск тормозной", "21120-3501070", "LADA", 2, 3600, 2450, False),
            ("Колодки передние", "11180-3501080", "Trialli", 1, 2100, 1350, True),
        ],
    },
    {
        "name": "Татьяна Орлова",
        "phone": "+79990001010",
        "source": LeadSource.TELEGRAM,
        "vin": "Z94C251CBJR123456",
        "car_info": "Hyundai Creta 2018",
        "status": LeadStatus.INVOICE,
        "days_ago": 9,
        "items": [
            ("Фара левая", "92101-M0000", "Hyundai", 1, 38500, 29800, False),
        ],
    },
    {
        "name": "Михаил Данилов",
        "phone": "+79990001011",
        "source": LeadSource.SITE,
        "vin": "XW8AN2NE9LH123456",
        "car_info": "Skoda Octavia 2020",
        "status": LeadStatus.INVOICE,
        "days_ago": 10,
        "items": [
            ("Радиатор охлаждения", "5Q0121251GN", "Nissens", 1, 24700, 18400, True),
            ("Антифриз 5 л", "G12E050A2", "VAG", 2, 3200, 2250, False),
        ],
    },
    {
        "name": "Виктория Лебедева",
        "phone": "+79990001012",
        "source": LeadSource.MANUAL,
        "vin": "X7M4SRAV50K123456",
        "car_info": "Renault Duster 2019",
        "status": LeadStatus.INVOICE,
        "days_ago": 11,
        "items": [
            ("Сцепление комплект", "302055852R", "Valeo", 1, 22800, 16900, True),
        ],
    },
    {
        "name": "Андрей Егоров",
        "phone": "+79990001013",
        "source": LeadSource.TELEGRAM,
        "vin": "XW7BK4FK30S123456",
        "car_info": "Toyota Camry 2021",
        "status": LeadStatus.WON,
        "days_ago": 14,
        "items": [
            ("Бампер передний", "52119-33B30", "Toyota", 1, 52000, 40500, False),
            ("Крепление бампера", "52535-33040", "Toyota", 2, 1800, 1100, False),
        ],
    },
    {
        "name": "Светлана Романова",
        "phone": "+79990001014",
        "source": LeadSource.SITE,
        "vin": "XW8ZZZ61ZJG123456",
        "car_info": "Volkswagen Polo 2018",
        "status": LeadStatus.WON,
        "days_ago": 18,
        "items": [
            ("Компрессор кондиционера", "6R0820803R", "Denso", 1, 46500, 35200, True),
        ],
    },
    {
        "name": "Павел Никитин",
        "phone": "+79990001015",
        "source": LeadSource.MANUAL,
        "vin": "XTA217230J0123456",
        "car_info": "Lada Priora 2018",
        "status": LeadStatus.LOST,
        "days_ago": 20,
        "items": [
            ("Генератор", "21700-3701010", "КЗАТЭ", 1, 15400, 12100, False),
        ],
    },
    {
        "name": "Ирина Семёнова",
        "phone": "+79990001016",
        "source": LeadSource.TELEGRAM,
        "vin": "Z94CB41AAHR123456",
        "car_info": "Kia Rio 2017",
        "status": LeadStatus.LOST,
        "days_ago": 24,
        "items": [
            ("Дверь передняя правая", "76004-H0000", "Kia", 1, 67000, 52000, False),
        ],
    },
]

STATUS_PATHS: dict[LeadStatus, list[LeadStatus]] = {
    LeadStatus.NEW: [],
    LeadStatus.IN_PROGRESS: [LeadStatus.IN_PROGRESS],
    LeadStatus.SELECTION: [LeadStatus.IN_PROGRESS, LeadStatus.SELECTION],
    LeadStatus.INVOICE: [
        LeadStatus.IN_PROGRESS,
        LeadStatus.SELECTION,
        LeadStatus.INVOICE,
    ],
    LeadStatus.WON: [
        LeadStatus.IN_PROGRESS,
        LeadStatus.SELECTION,
        LeadStatus.INVOICE,
        LeadStatus.WON,
    ],
    LeadStatus.LOST: [
        LeadStatus.IN_PROGRESS,
        LeadStatus.SELECTION,
        LeadStatus.INVOICE,
        LeadStatus.LOST,
    ],
}


async def upsert_user(session: Any, email: str, password: str, role: UserRole) -> User:
    user = await session.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, password_hash=hash_password(password), role=role)
        session.add(user)
        await session.flush()
        print(f"  created user: {email} ({role.value})")
    else:
        user.role = role
        user.password_hash = hash_password(password)
        print(f"  updated user: {email} ({role.value})")
    return user


async def create_demo_lead(session: Any, data: dict[str, Any], manager: User) -> bool:
    existing = await session.scalar(select(Lead).where(Lead.phone == data["phone"]))
    if existing is not None:
        return False

    created_at = datetime.now(UTC) - timedelta(days=data["days_ago"])
    lead = Lead(
        name=data["name"],
        phone=data["phone"],
        source=data["source"],
        vin=data["vin"],
        car_info=data["car_info"],
        status=data["status"],
        manager_id=manager.id,
        created_at=created_at,
        updated_at=created_at + timedelta(hours=4),
    )
    session.add(lead)
    await session.flush()

    for name, oem, brand, qty, price, purchase_price, is_analog in data["items"]:
        session.add(
            OrderItem(
                lead_id=lead.id,
                name=name,
                oem=oem,
                brand=brand,
                qty=qty,
                price=price,
                purchase_price=purchase_price,
                is_analog=is_analog,
            )
        )

    previous = LeadStatus.NEW
    for index, status in enumerate(STATUS_PATHS[data["status"]], start=1):
        session.add(
            StatusHistory(
                lead_id=lead.id,
                from_status=previous.value,
                to_status=status.value,
                changed_by=manager.id,
                changed_at=created_at + timedelta(hours=index),
            )
        )
        previous = status

    return True


async def seed() -> None:
    print("AutoCRM development seed")
    print("WARNING: default passwords are for local development only.\n")

    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            admin = await upsert_user(
                session, ADMIN_EMAIL, ADMIN_PASSWORD, UserRole.ADMIN
            )
            manager = await upsert_user(
                session, MANAGER_EMAIL, MANAGER_PASSWORD, UserRole.MANAGER
            )

            created_count = 0
            for data in DEMO_LEADS:
                if await create_demo_lead(session, data, manager):
                    created_count += 1

            await session.commit()
        except Exception:
            await session.rollback()
            raise

    await get_engine().dispose()

    print(f"\nDemo leads created: {created_count}")
    print(f"Admin:   {admin.email} / {ADMIN_PASSWORD}")
    print(f"Manager: {manager.email} / {MANAGER_PASSWORD}")
    print("Run the command again safely: demo rows will not be duplicated.")


if __name__ == "__main__":
    asyncio.run(seed())
