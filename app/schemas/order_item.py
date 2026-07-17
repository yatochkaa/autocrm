"""API-схемы позиций заказа и расчёта итогов."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, computed_field


class OrderItemBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
        title="Название детали",
        description="Наименование детали или позиции.",
        examples=["Тормозные колодки передние"],
    )
    oem: str | None = Field(
        default=None,
        max_length=100,
        title="OEM / артикул",
        description="OEM-номер производителя или артикул детали.",
        examples=["1K0698151"],
    )
    brand: str | None = Field(
        default=None,
        max_length=100,
        title="Бренд",
        description="Производитель детали.",
        examples=["Bosch"],
    )
    price: float | None = Field(
        default=None,
        ge=0,
        title="Цена продажи за единицу, ₽",
        description="Цена продажи одной единицы, в рублях.",
        examples=[4500],
    )
    purchase_price: float | None = Field(
        default=None,
        ge=0,
        title="Закупочная цена за единицу, ₽",
        description="Закупочная цена одной единицы, в рублях.",
        examples=[3200],
    )
    qty: int = Field(
        default=1,
        ge=1,
        title="Количество, шт.",
        description="Количество единиц позиции.",
        examples=[1],
    )
    is_analog: bool = Field(
        default=False,
        title="Аналог",
        description="false — оригинальная деталь, true — аналог.",
        examples=[False],
    )


class OrderItemCreate(OrderItemBase):
    """Данные для добавления позиции в заявку."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Тормозной диск передний",
                    "oem": "1K0615301AA",
                    "brand": "ATE",
                    "price": 5200,
                    "purchase_price": 3800,
                    "qty": 2,
                    "is_analog": False,
                },
                {
                    "name": "Тормозной диск передний (аналог)",
                    "oem": "DF4451",
                    "brand": "TRW",
                    "price": 3900,
                    "purchase_price": 2600,
                    "qty": 2,
                    "is_analog": True,
                },
            ]
        }
    )


class OrderItemUpdate(BaseModel):
    """Частичное обновление позиции заказа."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"price": 4100, "qty": 3}]}
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        title="Название детали",
        examples=["Тормозные колодки передние"],
    )
    oem: str | None = Field(
        default=None,
        max_length=100,
        title="OEM / артикул",
        examples=["1K0698151"],
    )
    brand: str | None = Field(
        default=None,
        max_length=100,
        title="Бренд",
        examples=["Bosch"],
    )
    price: float | None = Field(
        default=None,
        ge=0,
        title="Цена продажи за единицу, ₽",
        examples=[4100],
    )
    purchase_price: float | None = Field(
        default=None,
        ge=0,
        title="Закупочная цена за единицу, ₽",
        examples=[3200],
    )
    qty: int | None = Field(
        default=None,
        ge=1,
        title="Количество, шт.",
        examples=[3],
    )
    is_analog: bool | None = Field(
        default=None,
        title="Аналог",
        description="false — оригинал, true — аналог.",
        examples=[False],
    )


class OrderItemRead(OrderItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(title="ID позиции", examples=[1])
    lead_id: int = Field(title="ID заявки", examples=[1])

    @computed_field(
        title="Сумма позиции, ₽",
        description="Расчёт: line_total = price × qty (цена за единицу × кол-во).",
    )
    @property
    def line_total(self) -> float:
        return round((self.price or 0) * self.qty, 2)

    @computed_field(
        title="Маржа позиции, ₽",
        description=(
            "Расчёт: line_margin = (price − purchase_price) × qty. "
            "null, если не заданы цена или закупочная цена."
        ),
    )
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
