from sqlalchemy import Enum as SAEnum
from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import LeadSource, LeadStatus
from app.models.base import Base, TimestampMixin


def _enum_column(enum_cls: type) -> SAEnum:
    """Enum как VARCHAR + CHECK (native_enum=False) — портативно для SQLite и Postgres.

    values_callable хранит именно значения (\"new\"), а не имена (\"NEW\").
    """
    return SAEnum(
        enum_cls,
        native_enum=False,
        values_callable=lambda e: [m.value for m in e],
    )


class Lead(Base, TimestampMixin):
    """Заявка на запчасть — центральная сущность CRM."""

    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(200))
    contact: Mapped[str | None] = mapped_column(String(200), default=None)
    part_query: Mapped[str] = mapped_column(Text)  # что ищет клиент
    source: Mapped[LeadSource] = mapped_column(
        _enum_column(LeadSource), default=LeadSource.MANUAL
    )
    status: Mapped[LeadStatus] = mapped_column(
        _enum_column(LeadStatus), default=LeadStatus.NEW, index=True
    )
    # Деньги: Numeric для точности; asdecimal=False — отдаём float (простой JSON).
    sale_amount: Mapped[float | None] = mapped_column(
        Numeric(12, 2, asdecimal=False), default=None
    )
    cost_amount: Mapped[float | None] = mapped_column(
        Numeric(12, 2, asdecimal=False), default=None
    )
    comment: Mapped[str | None] = mapped_column(Text, default=None)

    @property
    def margin(self) -> float | None:
        """Маржа = продажа − закупка (если обе суммы заданы)."""
        if self.sale_amount is None or self.cost_amount is None:
            return None
        return self.sale_amount - self.cost_amount
