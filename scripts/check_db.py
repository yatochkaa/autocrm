"""Проверка моделей на РЕАЛЬНОЙ БД из DATABASE_URL (например, PostgreSQL в Docker).

В отличие от scripts/check_models.py (который всегда берёт SQLite в памяти),
этот скрипт подключается к той же БД, что и приложение.

Перед запуском нужно применить миграцию:  alembic upgrade head
Запуск:  python -m scripts.check_db
"""
from __future__ import annotations

from sqlalchemy import select

from app.db.enums import LeadSource, LeadStatus, UserRole
from app.db.models import Lead, OrderItem, User
from app.db.session import SessionLocal, engine


def main() -> None:
    print("Подключение:", engine.url.render_as_string(hide_password=True))

    with SessionLocal() as session:
        manager = User(email="docker@shop.ru", password_hash="x", role=UserRole.MANAGER)
        session.add(manager)
        session.flush()

        lead = Lead(
            name="Docker-тест",
            source=LeadSource.SITE,
            status=LeadStatus.NEW,
            manager_id=manager.id,
        )
        lead.items = [
            OrderItem(name="Фильтр масляный", oem="OC90", brand="Knecht", price=650, qty=2),
        ]
        session.add(lead)
        session.commit()

        found = session.scalars(
            select(Lead).where(Lead.name == "Docker-тест")
        ).all()
        print(f"Заявок в БД: {len(found)}; позиций у первой: {len(found[0].items)}")
        assert len(found) >= 1
        assert len(found[0].items) == 1

        # чистим за собой, чтобы повторный запуск был чистым
        for item in found:
            session.delete(item)
        session.delete(manager)
        session.commit()

    print("OK: подключение к реальной БД и модели работают")


if __name__ == "__main__":
    main()
