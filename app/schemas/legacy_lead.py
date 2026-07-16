"""Схемы старого API воронки заявок (этап 1)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import LeadSource, LeadStatus


class LegacyLeadBase(BaseModel):
    customer_name: str = Field(min_length=1, max_length=200)
    contact: str | None = Field(default=None, max_length=200)
    part_query: str = Field(min_length=1)
    source: LeadSource = LeadSource.MANUAL


class LegacyLeadCreate(LegacyLeadBase):
    sale_amount: float | None = Field(default=None, ge=0)
    cost_amount: float | None = Field(default=None, ge=0)
    comment: str | None = None


class LegacyLeadUpdate(BaseModel):
    customer_name: str | None = Field(default=None, min_length=1, max_length=200)
    contact: str | None = Field(default=None, max_length=200)
    part_query: str | None = Field(default=None, min_length=1)
    source: LeadSource | None = None
    sale_amount: float | None = Field(default=None, ge=0)
    cost_amount: float | None = Field(default=None, ge=0)
    comment: str | None = None


class LegacyLeadStatusUpdate(BaseModel):
    status: LeadStatus


class LegacyLeadRead(LegacyLeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: LeadStatus
    sale_amount: float | None
    cost_amount: float | None
    margin: float | None
    comment: str | None
    created_at: datetime
    updated_at: datetime
