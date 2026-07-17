"""app/schemas/lead.py  — FULL REPLACEMENT (Phase 2)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

LeadPriorityLiteral = Literal["low", "normal", "high", "urgent"]
LeadStatusLiteral = Literal["new", "in_progress", "selection", "invoice", "won", "lost"]
LeadSourceLiteral = Literal["manual", "telegram", "site"]


class LeadStatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lead_id: int
    from_status: str | None = None
    to_status: str
    changed_by: int | None = None  # поле в ORM StatusHistory
    changed_at: datetime | None = None


class LeadCreate(BaseModel):
    name: str
    phone: str | None = None
    vin: str | None = None
    car_info: str | None = None
    source: LeadSourceLiteral = "manual"
    priority: LeadPriorityLiteral = "normal"
    manager_id: int | None = None


class LeadUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    vin: str | None = None
    car_info: str | None = None
    source: LeadSourceLiteral | None = None
    priority: LeadPriorityLiteral | None = None
    manager_id: int | None = None
    rejection_reason: str | None = None


class LeadStatusUpdate(BaseModel):
    status: LeadStatusLiteral
    rejection_reason: str | None = None  # обязателен при status=lost


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    phone: str | None = None
    vin: str | None = None
    car_info: str | None = None
    source: str
    status: str
    priority: str = "normal"
    manager_id: int | None = None
    total_amount: float = 0.0
    total_margin: float | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    history: list[LeadStatusHistoryOut] = []
    # items живут в order_items.py — здесь не дублируем


class PaginatedLeads(BaseModel):
    items: list[LeadOut]
    total: int
    page: int
    limit: int
    pages: int


LeadRead = LeadOut
