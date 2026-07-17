"""Create 50–70 idempotent portfolio leads for AutoCRM."""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.core.database import get_session_factory
from app.db.enums import LeadSource, LeadStatus, UserRole
from app.db.models.audit_log import AuditLog
from app.db.models.lead import Lead
from app.db.models.order_item import OrderItem
from app.db.models.status_history import StatusHistory
from app.db.models.user import User

FIRST_NAMES = [
    "Александр", "Дмитрий", "Максим", "Иван", "Артём", "Михаил",
    "Никита", "Сергей", "Андрей", "Алексей", "Анна", "Мария",
    "Елена", "Ольга", "Наталья",
]
LAST_NAMES = [
    "Соколов", "Морозов", "Волков", "Лебедев", "Кузнецов", "Попов",
    "Новиков", "Фёдоров", "Орлов", "Макаров", "Белова", "Иванова",
    "Павлова", "Смирнова",
]
CARS = [
    "Lada Vesta 2021", "Toyota Camry 2019", "Kia Rio 2020",
    "Hyundai Solaris 2021", "Volkswagen Polo 2020", "Skoda Octavia 2018",
    "Ford Focus 2017", "Renault Logan 2019", "BMW 3 Series 2018",
    "Mercedes-Benz C-Class 2017", "Nissan Qashqai 2020", "Mazda CX-5 2019",
]
PARTS = [
    ("Колодки тормозные", "Brembo", 7800, 5100),
    ("Масло и фильтр", "MANN", 6400, 4300),
    ("Амортизатор", "KYB", 14200, 10100),
    ("Комплект сцепления", "LuK", 26800, 20800),
    ("Радиатор", "Denso", 18900, 13700),
    ("Подшипник ступицы", "SKF", 9600, 6800),
    ("Комплект ГРМ", "Gates", 12400, 8800),
    ("Фара", "Depo", 17300, 12600),
]
PORTFOLIO_PHONE_PREFIX = "+7999555"


def final_status(index: int) -> LeadStatus:
    bucket = index % 20
    if bucket < 3:
        return LeadStatus.NEW
    if bucket < 6:
        return LeadStatus.IN_PROGRESS
    if bucket < 9:
        return LeadStatus.SELECTION
    if bucket < 12:
        return LeadStatus.INVOICE
    if bucket < 18:
        return LeadStatus.WON
    return LeadStatus.LOST


def status_path(final: LeadStatus) -> list[LeadStatus]:
    active = [
        LeadStatus.NEW,
        LeadStatus.IN_PROGRESS,
        LeadStatus.SELECTION,
        LeadStatus.INVOICE,
    ]
    if final in (LeadStatus.WON, LeadStatus.LOST):
        return [*active, final]
    return active[: active.index(final) + 1]


def stage_durations(index: int, count: int) -> list[timedelta]:
    minutes = [
        30 + index % 151,
        90 + (index * 37) % 630,
        150 + (index * 53) % 1290,
        120 + (index * 71) % 2760,
    ]
    return [timedelta(minutes=value) for value in minutes[:count]]


async def seed(count: int, dry_run: bool = False) -> None:
    if not 50 <= count <= 70:
        raise SystemExit("--count должен быть от 50 до 70")

    async with get_session_factory()() as session:
        managers = list(
            (
                await session.scalars(
                    select(User)
                    .where(User.role == UserRole.MANAGER)
                    .order_by(User.id)
                )
            ).all()
        )
        if not managers:
            managers = list(
                (
                    await session.scalars(
                        select(User)
                        .where(User.role == UserRole.ADMIN)
                        .order_by(User.id)
                    )
                ).all()
            )
        if not managers:
            raise SystemExit("Сначала создайте пользователя")

        existing = int(
            await session.scalar(
                select(func.count(Lead.id)).where(
                    Lead.phone.like(f"{PORTFOLIO_PHONE_PREFIX}%")
                )
            )
            or 0
        )
        missing = max(0, count - existing)
        print(f"[portfolio] уже есть: {existing}; будет добавлено: {missing}")
        if dry_run or not missing:
            return

        now = datetime.now(UTC).replace(second=0, microsecond=0)
        for index in range(existing, count):
            final = final_status(index)
            path = status_path(final)
            durations = stage_durations(index, len(path) - 1)
            finished_at = now - timedelta(
                days=(index * 4) % 88,
                hours=(index * 3) % 20,
            )
            created_at = (
                finished_at - sum(durations, timedelta())
                if final in (LeadStatus.WON, LeadStatus.LOST)
                else now - timedelta(days=(index * 7) % 64, hours=(index * 5) % 20)
            )
            manager = managers[index % len(managers)]
            selected = (
                []
                if final in (LeadStatus.NEW, LeadStatus.IN_PROGRESS)
                else [PARTS[index % len(PARTS)]]
            )
            if selected and index % 3 == 0:
                selected.append(PARTS[(index + 3) % len(PARTS)])

            amount = sum(item[2] for item in selected)
            margin = sum(item[2] - item[3] for item in selected)
            lead = Lead(
                name=(
                    f"{FIRST_NAMES[index % len(FIRST_NAMES)]} "
                    f"{LAST_NAMES[(index * 3) % len(LAST_NAMES)]}"
                ),
                phone=f"{PORTFOLIO_PHONE_PREFIX}{index:04d}",
                source=[
                    LeadSource.TELEGRAM,
                    LeadSource.MANUAL,
                    LeadSource.SITE,
                ][index % 3],
                vin=f"XTA{index:014d}"[:17],
                car_info=CARS[index % len(CARS)],
                status=final,
                manager_id=manager.id,
                created_at=created_at,
                updated_at=created_at,
                priority=["low", "normal", "high", "urgent"][index % 4],
                rejection_reason=(
                    "Клиент отложил ремонт" if final == LeadStatus.LOST else None
                ),
                total_amount=float(amount),
                total_margin=float(margin),
            )
            session.add(lead)
            await session.flush()

            event_at = created_at
            session.add(
                StatusHistory(
                    lead_id=lead.id,
                    from_status=None,
                    to_status=LeadStatus.NEW.value,
                    changed_by=manager.id,
                    changed_at=event_at,
                )
            )
            session.add(
                AuditLog(
                    lead_id=lead.id,
                    actor_id=manager.id,
                    action="lead_created",
                    created_at=event_at,
                )
            )
            for step, target in enumerate(path[1:]):
                event_at += durations[step]
                previous = path[step]
                session.add(
                    StatusHistory(
                        lead_id=lead.id,
                        from_status=previous.value,
                        to_status=target.value,
                        changed_by=manager.id,
                        changed_at=event_at,
                    )
                )
                session.add(
                    AuditLog(
                        lead_id=lead.id,
                        actor_id=manager.id,
                        action="status_changed",
                        field="status",
                        old_value=previous.value,
                        new_value=target.value,
                        created_at=event_at,
                    )
                )
            lead.updated_at = event_at

            for number, (name, brand, price, purchase) in enumerate(selected, 1):
                session.add(
                    OrderItem(
                        lead_id=lead.id,
                        oem=f"OEM-{index:03d}-{number}",
                        brand=brand,
                        name=name,
                        price=price,
                        purchase_price=purchase,
                        qty=1,
                        is_analog=number > 1,
                    )
                )

        await session.commit()
        total = int(await session.scalar(select(func.count(Lead.id))) or 0)
        print(f"[portfolio] готово: добавлено {missing}; всего заявок: {total}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Добавить реалистичные заявки для портфолио"
    )
    parser.add_argument("--count", type=int, default=60)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(seed(args.count, args.dry_run))


if __name__ == "__main__":
    main()
