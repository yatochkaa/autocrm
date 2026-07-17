"""API-схемы заявки."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.db.enums import LeadSource, LeadStatus
from app.schemas.order_item import OrderItemCreate, OrderItemRead
from app.schemas.status_history import StatusHistoryRead


class LeadBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=200,
        title="Имя клиента",
        description="ФИО или имя клиента по заявке.",
        examples=["Иван Петров"],
    )
    phone: str | None = Field(
        default=None,
        max_length=50,
        title="Телефон",
        description="Контактный телефон клиента.",
        examples=["+7 900 123-45-67"],
    )
    source: LeadSource = Field(
        default=LeadSource.MANUAL,
        title="Источник заявки",
        description=(
            "Канал заявки: telegram — Telegram, " "manual — вручную, site — сайт."
        ),
        examples=["site"],
    )
    vin: str | None = Field(
        default=None,
        max_length=64,
        title="VIN автомобиля",
        description="VIN-номер автомобиля клиента (17 символов).",
        examples=["WVWZZZ1KZAW000001"],
    )
    car_info: str | None = Field(
        default=None,
        max_length=255,
        title="Информация об автомобиле",
        description="Марка, модель, год выпуска и двигатель.",
        examples=["Volkswagen Golf 2019, 1.4 TSI"],
    )
    manager_id: int | None = Field(
        default=None,
        title="Ответственный менеджер",
        description="ID менеджера, ответственного за заявку.",
        examples=[1],
    )


class LeadCreate(LeadBase):
    """Данные для создания заявки."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Иван Петров",
                    "phone": "+7 900 123-45-67",
                    "source": "site",
                    "vin": "WVWZZZ1KZAW000001",
                    "car_info": "Volkswagen Golf 2019, 1.4 TSI",
                    "manager_id": 1,
                    "items": [
                        {
                            "name": "Тормозные колодки передние",
                            "oem": "1K0698151",
                            "brand": "Bosch",
                            "price": 4500,
                            "purchase_price": 3200,
                            "qty": 1,
                            "is_analog": False,
                        }
                    ],
                }
            ]
        }
    )

    items: list[OrderItemCreate] = Field(
        default_factory=list,
        title="Позиции заказа",
        description="Список позиций заявки. Можно оставить пустым.",
    )


class LeadUpdate(BaseModel):
    """Частичное обновление заявки."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Иван Петров",
                    "phone": "+7 900 765-43-21",
                    "manager_id": 2,
                }
            ]
        }
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        title="Имя клиента",
        description="ФИО или имя клиента по заявке.",
        examples=["Иван Петров"],
    )
    phone: str | None = Field(
        default=None,
        max_length=50,
        title="Телефон",
        description="Контактный телефон клиента.",
        examples=["+7 900 765-43-21"],
    )
    source: LeadSource | None = Field(
        default=None,
        title="Источник заявки",
        description="Канал заявки: telegram, manual или site.",
        examples=["site"],
    )
    vin: str | None = Field(
        default=None,
        max_length=64,
        title="VIN автомобиля",
        description="VIN-номер автомобиля клиента.",
        examples=["WVWZZZ1KZAW000001"],
    )
    car_info: str | None = Field(
        default=None,
        max_length=255,
        title="Информация об автомобиле",
        description="Марка, модель, год выпуска и двигатель.",
        examples=["Volkswagen Golf 2019, 1.4 TSI"],
    )
    manager_id: int | None = Field(
        default=None,
        title="Ответственный менеджер",
        description="ID менеджера, ответственного за заявку.",
        examples=[2],
    )


class LeadStatusUpdate(BaseModel):
    """Смена статуса заявки по воронке."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"status": "in_progress"}]}
    )

    status: LeadStatus = Field(
        title="Статус воронки",
        description=(
            "Новый статус заявки. Допустимая цепочка переходов: "
            "new → in_progress → selection → invoice → won/lost."
        ),
        examples=["in_progress"],
    )


class LeadRead(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(title="ID заявки", examples=[1])
    status: LeadStatus = Field(
        title="Статус воронки",
        description="Текущий статус заявки в воронке.",
        examples=["new"],
    )
    created_at: datetime = Field(title="Дата создания")
    updated_at: datetime = Field(title="Дата последнего изменения")
    items: list[OrderItemRead] = Field(default_factory=list, title="Позиции заказа")
    history: list[StatusHistoryRead] = Field(
        default_factory=list, title="История статусов"
    )

    @computed_field(
        title="Сумма оригиналов, ₽",
        description="Сумма line_total по позициям-оригиналам (is_analog = false).",
    )
    @property
    def original_total(self) -> float:
        return round(
            sum(item.line_total for item in self.items if not item.is_analog), 2
        )

    @computed_field(
        title="Сумма аналогов, ₽",
        description="Сумма line_total по позициям-аналогам (is_analog = true).",
    )
    @property
    def analog_total(self) -> float:
        return round(sum(item.line_total for item in self.items if item.is_analog), 2)

    @computed_field(
        title="Итоговая сумма, ₽",
        description="Сумма line_total по всем позициям заявки.",
    )
    @property
    def total_amount(self) -> float:
        return round(sum(item.line_total for item in self.items), 2)

    @computed_field(
        title="Итоговая маржа, ₽",
        description="Сумма line_margin по позициям, где маржу можно рассчитать.",
    )
    @property
    def total_margin(self) -> float | None:
        margins = [
            item.line_margin for item in self.items if item.line_margin is not None
        ]
        return round(sum(margins), 2) if margins else None
