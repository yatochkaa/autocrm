"""app/db/enums.py  — FULL REPLACEMENT (Phase 2).
Добавлен LeadPriority. Остальные enum-ы не изменены.
"""

import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"


class LeadStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    SELECTION = "selection"
    INVOICE = "invoice"
    WON = "won"
    LOST = "lost"


class LeadSource(str, enum.Enum):
    MANUAL = "manual"
    TELEGRAM = "telegram"
    SITE = "site"


class LeadPriority(str, enum.Enum):  # NEW
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
