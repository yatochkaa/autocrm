"""Схемы заявки (create / read / update / status update)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.enums import LeadSource, LeadStatus
from app.domain.enums import LeadStatus as FunnelLeadStatus
from app.schemas.order_item import OrderItemCreate, OrderItemRead


class LeadBase(BaseModel):
    name: str = Field(max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    source: LeadSource = LeadSource.MANUAL
    vin: str | None = Field(default=None, max_length=17)
    car_info: str | None = Field(default=None, max_length=255)
    manager_id: int | None = None


class LeadCreate(LeadBase):
    items: list[OrderItemCreate] = Field(default_factory=list)


class LeadUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    source: LeadSource | None = None
    vin: str | None = Field(default=None, max_length=17)
    car_info: str | None = Field(default=None, max_length=255)
    status: LeadStatus | None = None
    manager_id: int | None = None


class LeadStatusUpdate(BaseModel):
    """Совместимость с API воронки из предыдущего этапа."""

    status: FunnelLeadStatus


class LeadRead(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: LeadStatus
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead] = Field(default_factory=list)
