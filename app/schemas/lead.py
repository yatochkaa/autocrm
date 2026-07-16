"""API-схемы заявки."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.enums import LeadSource, LeadStatus
from app.schemas.order_item import OrderItemCreate, OrderItemRead
from app.schemas.status_history import StatusHistoryRead


class LeadBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    source: LeadSource = LeadSource.MANUAL
    vin: str | None = Field(default=None, max_length=64)
    car_info: str | None = Field(default=None, max_length=255)
    manager_id: int | None = None


class LeadCreate(LeadBase):
    items: list[OrderItemCreate] = Field(default_factory=list)


class LeadUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    source: LeadSource | None = None
    vin: str | None = Field(default=None, max_length=64)
    car_info: str | None = Field(default=None, max_length=255)
    manager_id: int | None = None


class LeadStatusUpdate(BaseModel):
    status: LeadStatus


class LeadRead(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: LeadStatus
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead] = Field(default_factory=list)
    history: list[StatusHistoryRead] = Field(default_factory=list)
