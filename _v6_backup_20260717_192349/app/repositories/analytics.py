"""SQLAlchemy queries for analytics; sales use WON transition time."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from sqlalchemy import distinct,func,select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.enums import LeadStatus
from app.db.models.lead import Lead
from app.db.models.order_item import OrderItem
from app.db.models.status_history import StatusHistory
from app.db.models.user import User

class AnalyticsRepository:
    def __init__(self,session:AsyncSession)->None:self.session=session
    @staticmethod
    def _created_filter(date_from:datetime,date_to:datetime):return (Lead.created_at>=date_from,Lead.created_at<date_to)
    @staticmethod
    def _won_ids(date_from:datetime,date_to:datetime):
        return select(StatusHistory.lead_id.label("lead_id")).where(StatusHistory.to_status==LeadStatus.WON.value,StatusHistory.changed_at>=date_from,StatusHistory.changed_at<date_to).distinct().subquery()
    async def overview(self,date_from:datetime,date_to:datetime)->tuple[int,int,float]:
        total=await self.session.scalar(select(func.count(Lead.id)).where(*self._created_filter(date_from,date_to)))
        won=self._won_ids(date_from,date_to)
        sales=await self.session.scalar(select(func.count()).select_from(won))
        revenue_value=await self.session.scalar(select(func.coalesce(func.sum(OrderItem.price*OrderItem.qty),0)).select_from(won).join(Lead,Lead.id==won.c.lead_id).join(OrderItem,OrderItem.lead_id==Lead.id,isouter=True))
        return int(total or 0),int(sales or 0),float(revenue_value or Decimal("0"))
    async def sources(self,date_from:datetime,date_to:datetime)->list[tuple[object,int]]:
        rows=(await self.session.execute(select(Lead.source,func.count(Lead.id)).where(*self._created_filter(date_from,date_to)).group_by(Lead.source))).all()
        return [(source,int(count)) for source,count in rows]
    async def managers(self,date_from:datetime,date_to:datetime,limit:int)->list[tuple[int,str,int,float]]:
        won=self._won_ids(date_from,date_to);sales_count=func.count(distinct(Lead.id));revenue=func.coalesce(func.sum(OrderItem.price*OrderItem.qty),0)
        statement=select(User.id,User.email,sales_count,revenue).select_from(won).join(Lead,Lead.id==won.c.lead_id).join(User,User.id==Lead.manager_id).join(OrderItem,OrderItem.lead_id==Lead.id,isouter=True).group_by(User.id,User.email).order_by(sales_count.desc(),revenue.desc(),User.id).limit(limit)
        return [(int(i),e,int(s),float(r or 0)) for i,e,s,r in (await self.session.execute(statement)).all()]
    async def stage_history(self,date_from:datetime,date_to:datetime)->list[tuple[int,datetime,str|None,str,datetime]]:
        history=select(
            StatusHistory.lead_id.label("lead_id"),
            StatusHistory.from_status.label("from_status"),
            StatusHistory.to_status.label("to_status"),
            StatusHistory.changed_at.label("changed_at"),
            func.lag(StatusHistory.changed_at).over(
                partition_by=StatusHistory.lead_id,
                order_by=(StatusHistory.changed_at,StatusHistory.id),
            ).label("previous_changed_at"),
        ).subquery()
        statement=(
            select(
                history.c.lead_id,
                func.coalesce(history.c.previous_changed_at,Lead.created_at).label("entered_at"),
                history.c.from_status,
                history.c.to_status,
                history.c.changed_at,
            )
            .join(Lead,Lead.id==history.c.lead_id)
            .where(history.c.changed_at>=date_from,history.c.changed_at<date_to)
            .order_by(history.c.lead_id,history.c.changed_at)
        )
        return list((await self.session.execute(statement)).all())
