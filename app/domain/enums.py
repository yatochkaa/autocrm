from enum import StrEnum


class LeadStatus(StrEnum):
    """Стадии воронки продаж по заявке на запчасть."""

    NEW = "new"  # Новая
    IN_PROGRESS = "in_progress"  # В работе
    SELECTION = "selection"  # Подбор
    INVOICE = "invoice"  # Счёт
    WON = "won"  # Продажа
    LOST = "lost"  # Отказ


class LeadSource(StrEnum):
    """Откуда пришла заявка."""

    TELEGRAM = "telegram"  # Из Telegram-бота
    MANUAL = "manual"  # Заведена менеджером вручную
    WEBSITE = "website"  # С формы на сайте
