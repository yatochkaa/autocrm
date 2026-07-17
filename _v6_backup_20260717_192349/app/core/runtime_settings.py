"""Persisted runtime settings and automatic priority ageing."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class RuntimeSettings(BaseModel):
    auto_priority_enabled: bool = True
    normal_after_minutes: int = Field(default=60, ge=0, le=525600)
    high_after_minutes: int = Field(default=180, ge=1, le=525600)
    urgent_after_minutes: int = Field(default=420, ge=2, le=525600)

SETTINGS_PATH = Path.cwd() / "autocrm_settings.json"
DEFAULTS = RuntimeSettings()

def load_runtime_settings() -> RuntimeSettings:
    if not SETTINGS_PATH.exists(): return DEFAULTS.model_copy()
    try:
        raw=json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        if "normal_after_days" in raw:
            raw={"auto_priority_enabled":raw.get("auto_priority_enabled",True),"normal_after_minutes":int(raw.get("normal_after_days",1))*1440,"high_after_minutes":int(raw.get("high_after_days",3))*1440,"urgent_after_minutes":int(raw.get("urgent_after_days",7))*1440}
        return RuntimeSettings.model_validate(raw)
    except (OSError,ValueError,TypeError): return DEFAULTS.model_copy()

def save_runtime_settings(value: RuntimeSettings) -> RuntimeSettings:
    temp=SETTINGS_PATH.with_suffix(".json.tmp")
    temp.write_text(json.dumps(value.model_dump(),ensure_ascii=False,indent=2),encoding="utf-8")
    temp.replace(SETTINGS_PATH); return value

def priority_for_age(created_at: datetime, settings: RuntimeSettings) -> str:
    created=created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
    age=max(0,int((datetime.now(timezone.utc)-created).total_seconds()//60))
    if age>=settings.urgent_after_minutes:return "urgent"
    if age>=settings.high_after_minutes:return "high"
    if age>=settings.normal_after_minutes:return "normal"
    return "low"

async def refresh_auto_priorities(session: AsyncSession, lead_id: int|None=None) -> int:
    settings=load_runtime_settings()
    if not settings.auto_priority_enabled:return 0
    from app.db.models.lead import Lead
    statement=select(Lead).where(Lead.status.notin_(["won","lost"]))
    if lead_id is not None:statement=statement.where(Lead.id==lead_id)
    changed=0
    for lead in (await session.scalars(statement)).all():
        expected=priority_for_age(lead.created_at,settings)
        if lead.priority!=expected:lead.priority=expected;changed+=1
    if changed:await session.commit()
    return changed
