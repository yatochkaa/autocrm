"""app/schemas/audit_log.py  — NEW FILE (Phase 2)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lead_id: int | None = None
    actor_id: int | None = None
    action: str
    field: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    meta: str | None = None
    created_at: datetime
