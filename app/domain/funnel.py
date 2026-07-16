"""Правила переходов по воронке AutoCRM."""
from __future__ import annotations

from app.db.enums import LeadStatus

ALLOWED_TRANSITIONS: dict[LeadStatus, set[LeadStatus]] = {
    LeadStatus.NEW: {LeadStatus.IN_PROGRESS},
    LeadStatus.IN_PROGRESS: {LeadStatus.SELECTION},
    LeadStatus.SELECTION: {LeadStatus.INVOICE},
    LeadStatus.INVOICE: {LeadStatus.WON, LeadStatus.LOST},
    LeadStatus.WON: set(),
    LeadStatus.LOST: set(),
}


class InvalidTransition(ValueError):
    def __init__(self, current: LeadStatus, target: LeadStatus) -> None:
        super().__init__(f"Недопустимый переход: {current.value} -> {target.value}")


def can_transition(current: LeadStatus, target: LeadStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


def validate_transition(current: LeadStatus, target: LeadStatus) -> None:
    if not can_transition(current, target):
        raise InvalidTransition(current, target)
