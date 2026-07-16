"""Схемы истории статусов (create / read). Обновление не предусмотрено:
история только дополняется."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StatusHistoryBase(BaseModel):
    from_status: str | None = None
    to_status: str
    changed_by: int | None = None


class StatusHistoryCreate(StatusHistoryBase):
    pass


class StatusHistoryRead(StatusHistoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    changed_at: datetime
