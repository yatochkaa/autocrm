"""Idempotent development seed for AutoCRM Phase 2.

Credentials are read from SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD and
SEED_MANAGER_EMAIL / SEED_MANAGER_PASSWORD. Existing users are preserved.
"""

from __future__ import annotations

import asyncio
import os
import random
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session_factory
from app.core.security import hash_password
from app.db.enums import LeadSource, LeadStatus, UserRole
from app.db.models import AuditLog, Lead, OrderItem, StatusHistory, User
from app.db.models.comment import Comment

ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "volgarec999@mail.ru")
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "admin123")
MANAGER_EMAIL = os.getenv("SEED_MANAGER_EMAIL", "manager@autocrm.local")
MANAGER_PASSWORD = os.getenv("SEED_MANAGER_PASSWORD", "manager123")
UPDATE_PASSWORDS = os.getenv("SEED_UPDATE_PASSWORDS", "0") == "1"

NAMES = [
    "Иван Петров",
    "Мария Сидорова",
    "Алексей Кузнецов",
    "Ольга Новикова",
    "Дмитрий Волков",
    "Елена Соколова",
    "Андрей Морозов",
    "Татьяна Лебедева",
    "Николай Козлов",
    "Светлана Попова",
    "Владимир Зайцев",
    "Наталья Рыжова",
    "Сергей Борисов",
    "Анна Шевченко",
    "Павел Крылов",
    "Ирина Орлова",
    "Роман Фёдоров",
    "Виктория Белова",
]
CARS = [
    ("XTA210930L2700001", "Lada Granta 2023"),
    ("XTAFB21130Y000001", "Toyota Camry 2021"),
    ("X7LSRBL1HEZ123456", "BMW X5 2022"),
    ("WBAVD13598KX12345", "BMW 3 Series 2020"),
    ("JF1GD7964JG800001", "Subaru Impreza 2020"),
    ("KMHCT41ABFU012345", "Hyundai Accent 2019"),
]
PARTS = [
    ("Масляный фильтр", "0451103316", "BOSCH", 1, 850.0, 600.0),
    ("Тормозные колодки", "D1060-9N00A", "NISSAN", 1, 3900.0, 2600.0),
    ("Воздушный фильтр", "28113-2B000", "HYUNDAI", 1, 1200.0, 760.0),
    ("Свечи зажигания", "22401-AA570", "SUBARU", 4, 720.0, 480.0),
    ("Амортизатор", "54302-EZ40A", "NISSAN", 2, 6900.0, 4700.0),
    ("Радиатор", "16400-28130", "TOYOTA", 1, 12800.0, 9000.0),
]
STATUSES = [
    LeadStatus.NEW,
    LeadStatus.IN_PROGRESS,
    LeadStatus.SELECTION,
    LeadStatus.INVOICE,
    LeadStatus.WON,
    LeadStatus.LOST,
]
PRIORITIES = ["low", "normal", "normal", "high", "urgent"]


async def upsert_user(
    session: AsyncSession, email: str, password: str, role: UserRole
) -> User:
    user = await session.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, password_hash=hash_password(password), role=role)
        session.add(user)
        await session.flush()
    elif UPDATE_PASSWORDS:
        user.password_hash = hash_password(password)
        user.role = role
    return user


async def seed(session: AsyncSession) -> None:
    admin = await upsert_user(session, ADMIN_EMAIL, ADMIN_PASSWORD, UserRole.ADMIN)
    manager = await upsert_user(
        session, MANAGER_EMAIL, MANAGER_PASSWORD, UserRole.MANAGER
    )

    lead_count = await session.scalar(select(func.count(Lead.id)))
    if lead_count:
        await session.commit()
        print(
            f"[seed] users ready; {lead_count} leads already exist, demo leads skipped"
        )
        return

    rng = random.Random(42)
    now = datetime.now(UTC)
    for index, name in enumerate(NAMES):
        status = STATUSES[index % len(STATUSES)]
        vin, car_info = CARS[index % len(CARS)]
        selected_parts = rng.sample(PARTS, k=2 + index % 2)
        total_amount = sum(qty * price for _, _, _, qty, price, _ in selected_parts)
        total_margin = sum(
            qty * (price - purchase_price)
            for _, _, _, qty, price, purchase_price in selected_parts
        )
        lead = Lead(
            name=name,
            phone=(
                f"+7 9{10 + index:02d} {100 + index:03d}-"
                f"{20 + index:02d}-{30 + index:02d}"
            ),
            source=list(LeadSource)[index % len(LeadSource)],
            status=status,
            priority=PRIORITIES[index % len(PRIORITIES)],
            vin=vin,
            car_info=car_info,
            manager_id=manager.id,
            rejection_reason="Клиент выбрал другое предложение"
            if status == LeadStatus.LOST
            else None,
            total_amount=round(total_amount, 2),
            total_margin=round(total_margin, 2),
        )
        session.add(lead)
        await session.flush()

        for part_name, oem, brand, qty, price, purchase_price in selected_parts:
            session.add(
                OrderItem(
                    lead_id=lead.id,
                    name=part_name,
                    oem=oem,
                    brand=brand,
                    qty=qty,
                    price=price,
                    purchase_price=purchase_price,
                    is_analog=False,
                )
            )
        session.add(
            StatusHistory(
                lead_id=lead.id,
                from_status=None,
                to_status=status.value,
                changed_by=admin.id,
                changed_at=now,
            )
        )
        session.add(
            AuditLog(
                lead_id=lead.id,
                actor_id=admin.id,
                action="create",
                new_value=status.value,
            )
        )
        if index < 6:
            session.add(
                Comment(
                    lead_id=lead.id,
                    author_id=manager.id,
                    text="Связались с клиентом, уточняем детали заказа.",
                )
            )

    await session.commit()
    print(
        f"[seed] created {len(NAMES)} leads; "
        f"admin={ADMIN_EMAIL}; manager={MANAGER_EMAIL}"
    )


async def main() -> None:
    async with get_session_factory()() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())
