"""API-схемы позиций заказа и расчёта итогов."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, computed_field


class OrderItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    oem: str | None = Field(default=None, max_length=100)
    brand: str | None = Field(default=None, max_length=100)
    price: float | None = Field(default=None, ge=0)
    purchase_price: float | None = Field(default=None, ge=0)
    qty: int = Field(default=1, ge=1)
    is_analog: bool = False


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    oem: str | None = Field(default=None, max_length=100)
    brand: str | None = Field(default=None, max_length=100)
    price: float | None = Field(default=None, ge=0)
    purchase_price: float | None = Field(default=None, ge=0)
    qty: int | None = Field(default=None, ge=1)
    is_analog: bool | None = None


class OrderItemRead(OrderItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int

    @computed_field
    @property
    def line_total(self) -> float:
        return round((self.price or 0) * self.qty, 2)

    @computed_field
    @property
    def line_margin(self) -> float | None:
        if self.price is None or self.purchase_price is None:
            return None
        return round((self.price - self.purchase_price) * self.qty, 2)


class OrderItemsSummary(BaseModel):
    items: list[OrderItemRead]
    original_items: list[OrderItemRead]
    analog_items: list[OrderItemRead]
    original_total: float
    analog_total: float
    total_amount: float
    total_margin: float | None

    @classmethod
    def build(cls, items: list[OrderItemRead]) -> OrderItemsSummary:
        original_items = [item for item in items if not item.is_analog]
        analog_items = [item for item in items if item.is_analog]
        margins = [item.line_margin for item in items if item.line_margin is not None]
        return cls(
            items=items,
            original_items=original_items,
            analog_items=analog_items,
            original_total=round(sum(item.line_total for item in original_items), 2),
            analog_total=round(sum(item.line_total for item in analog_items), 2),
            total_amount=round(sum(item.line_total for item in items), 2),
            total_margin=round(sum(margins), 2) if margins else None,
        )
