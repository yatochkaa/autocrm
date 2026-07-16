"""Тесты моделей этапа 2 (in-memory SQLite, без внешней БД)."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.enums import LeadSource, LeadStatus, UserRole
from app.db.models import Comment, Lead, OrderItem, StatusHistory, User


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _seed(session) -> Lead:
    manager = User(email="m@shop.ru", password_hash="x", role=UserRole.MANAGER)
    session.add(manager)
    session.flush()
    lead = Lead(
        name="Иван",
        source=LeadSource.TELEGRAM,
        status=LeadStatus.NEW,
        manager_id=manager.id,
    )
    lead.items = [
        OrderItem(name="Колодки", oem="1K0698151", brand="Bosch", price=2500, qty=1),
        OrderItem(
            name="Аналог", oem="1K0698151", brand="TRW", price=1800, is_analog=True
        ),
    ]
    lead.comments = [Comment(text="Перезвонить", author_id=manager.id)]
    lead.history = [StatusHistory(to_status="new", changed_by=manager.id)]
    session.add(lead)
    session.commit()
    return lead


def test_relationships(session):
    lead = _seed(session)
    loaded = session.get(Lead, lead.id)
    assert loaded.manager.email == "m@shop.ru"
    assert len(loaded.items) == 2
    assert {i.is_analog for i in loaded.items} == {True, False}
    assert loaded.comments[0].author.role == UserRole.MANAGER
    assert loaded.history[0].to_status == "new"


def test_cascade_delete(session):
    lead = _seed(session)
    session.delete(lead)
    session.commit()
    assert session.query(OrderItem).count() == 0
    assert session.query(Comment).count() == 0
    assert session.query(StatusHistory).count() == 0
    assert session.query(User).count() == 1  # менеджер остаётся
