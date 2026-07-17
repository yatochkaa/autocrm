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
    TELEGRAM = "telegram"
    MANUAL = "manual"
    SITE = "site"


class LeadPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"