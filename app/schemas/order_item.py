"""Схемы позиции подбора (create / read / update)."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class OrderItemBase(BaseModel):
    name: str = Field(max_length=255)
    oem: str | None = Field(default=None, max_length=100)
    brand: str | None = Field(default=None, max_length=100)
    price: float | None = Field(default=None, ge=0)
    qty: int = Field(default=1, ge=1)
    is_analog: bool = False


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    oem: str | None = Field(default=None, max_length=100)
    brand: str | None = Field(default=None, max_length=100)
    price: float | None = Field(default=None, ge=0)
    qty: int | None = Field(default=None, ge=1)
    is_analog: bool | None = None


class OrderItemRead(OrderItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
