"""Перечисления (enum) для доменных полей.

Значения хранятся в БД как строки (native_enum=False в моделях),
поэтому переезд между СУБД (SQLite <-> PostgreSQL) не требует правки типов.
"""

from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    """Роль пользователя системы."""

    ADMIN = "admin"
    MANAGER = "manager"


class LeadSource(str, enum.Enum):
    """Откуда пришла заявка."""

    TELEGRAM = "telegram"
    MANUAL = "manual"
    SITE = "site"


class LeadStatus(str, enum.Enum):
    """Статусы воронки продаж."""

    NEW = "new"
    IN_PROGRESS = "in_progress"
    SELECTION = "selection"
    INVOICE = "invoice"
    WON = "won"
    LOST = "lost"
