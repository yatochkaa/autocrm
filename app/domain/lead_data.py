"""Нормализация телефона и распознавание VIN."""

from __future__ import annotations

import re

VIN_PATTERN = re.compile(r"(?<![A-Z0-9])([A-HJ-NPR-Z0-9]{17})(?![A-Z0-9])")


class LeadDataError(ValueError):
    """Некорректные контактные данные заявки."""


def normalize_phone(phone: str | None) -> str | None:
    """Приводит российский номер к +7XXXXXXXXXX."""
    if phone is None or not phone.strip():
        return None

    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits[0] in {"7", "8"}:
        return f"+7{digits[1:]}"
    if len(digits) == 10:
        return f"+7{digits}"
    raise LeadDataError("Телефон должен содержать 10 цифр или начинаться с 7/8")


def normalize_vin(vin: str) -> str:
    """Нормализует VIN и проверяет длину/допустимые символы."""
    normalized = re.sub(r"[\s-]", "", vin).upper()
    if len(normalized) != 17:
        raise LeadDataError("VIN должен содержать ровно 17 символов")
    if not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", normalized):
        raise LeadDataError("VIN содержит недопустимые символы I, O, Q или знаки")
    return normalized


def extract_vin(text: str | None) -> str | None:
    """Ищет первый VIN в произвольном тексте."""
    if not text:
        return None
    match = VIN_PATTERN.search(text.upper())
    return match.group(1) if match else None


def resolve_vin(explicit_vin: str | None, *texts: str | None) -> str | None:
    """Берёт явный VIN либо извлекает его из переданных текстов."""
    if explicit_vin:
        return normalize_vin(explicit_vin)
    for text in texts:
        found = extract_vin(text)
        if found:
            return found
    return None
