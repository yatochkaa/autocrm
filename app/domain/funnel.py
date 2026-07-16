from app.domain.enums import LeadStatus

# Разрешённые переходы по воронке. Пустое множество — терминальный статус.
ALLOWED_TRANSITIONS: dict[LeadStatus, set[LeadStatus]] = {
    LeadStatus.NEW: {LeadStatus.IN_PROGRESS, LeadStatus.LOST},
    LeadStatus.IN_PROGRESS: {LeadStatus.SELECTION, LeadStatus.LOST},
    LeadStatus.SELECTION: {LeadStatus.INVOICE, LeadStatus.LOST},
    LeadStatus.INVOICE: {LeadStatus.WON, LeadStatus.LOST},
    LeadStatus.WON: set(),
    LeadStatus.LOST: set(),
}


class FunnelError(Exception):
    """Нарушение бизнес-правил воронки."""


class InvalidTransition(FunnelError):
    """Попытка недопустимого перехода между статусами."""

    def __init__(self, current: LeadStatus, target: LeadStatus) -> None:
        super().__init__(
            f"Недопустимый переход: {current.value} → {target.value}"
        )
        self.current = current
        self.target = target


def can_transition(current: LeadStatus, target: LeadStatus) -> bool:
    """True, если переход current → target разрешён воронкой."""
    return target in ALLOWED_TRANSITIONS.get(current, set())
