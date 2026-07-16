"""Мини-проверка моделей этапа 2 без внешней БД.

Создаёт таблицы во временной SQLite в памяти, добавляет пользователя,
заявку с позициями, комментарий и запись истории, затем проверяет связи.

Запуск из корня проекта:
    python -m scripts.check_models
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.enums import LeadSource, LeadStatus, UserRole
from app.db.models import Comment, Lead, OrderItem, StatusHistory, User


def main() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        manager = User(email="m@shop.ru", password_hash="x", role=UserRole.MANAGER)
        session.add(manager)
        session.flush()  # получаем manager.id

        lead = Lead(
            name="Иван",
            phone="+7999",
            source=LeadSource.TELEGRAM,
            vin="XW8ZZZ3CZEG000000",
            car_info="VW Passat B7 2013",
            status=LeadStatus.NEW,
            manager_id=manager.id,
        )
        lead.items = [
            OrderItem(name="Колодки", oem="1K0698151", brand="Bosch", price=2500, qty=1),
            OrderItem(name="Колодки аналог", oem="1K0698151", brand="TRW", price=1800, is_analog=True),
        ]
        lead.comments = [Comment(text="Клиент просит перезвонить", author_id=manager.id)]
        lead.history = [StatusHistory(from_status=None, to_status="new", changed_by=manager.id)]
        session.add(lead)
        session.commit()

        loaded = session.get(Lead, lead.id)
        assert loaded is not None
        assert loaded.manager is manager, "lead.manager должен ссылаться на менеджера"
        assert len(loaded.items) == 2, "у заявки должно быть 2 позиции"
        assert loaded.items[0].lead is loaded, "обратная связь item.lead"
        assert len(loaded.comments) == 1, "должен быть 1 комментарий"
        assert len(loaded.history) == 1, "должна быть 1 запись истории"
        assert manager.leads[0] is loaded, "manager.leads должен содержать заявку"

    print("OK: модели и связи этапа 2 работают корректно")


if __name__ == "__main__":
    main()
