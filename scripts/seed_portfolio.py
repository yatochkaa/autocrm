from __future__ import annotations
import argparse,asyncio
from datetime import UTC,datetime,timedelta
from sqlalchemy import func,select
from app.core.database import get_session_factory
from app.db.enums import LeadSource,LeadStatus,UserRole
from app.db.models.audit_log import AuditLog
from app.db.models.lead import Lead
from app.db.models.order_item import OrderItem
from app.db.models.status_history import StatusHistory
from app.db.models.user import User
FIRST=['Александр','Дмитрий','Максим','Иван','Артём','Михаил','Никита','Сергей','Андрей','Алексей','Анна','Мария','Елена','Ольга','Наталья']
LAST=['Соколов','Морозов','Волков','Лебедев','Кузнецов','Попов','Новиков','Фёдоров','Орлов','Макаров','Белова','Иванова','Павлова','Смирнова']
CARS=['Lada Vesta 2021','Toyota Camry 2019','Kia Rio 2020','Hyundai Solaris 2021','Volkswagen Polo 2020','Skoda Octavia 2018','Ford Focus 2017','Renault Logan 2019','BMW 3 Series 2018','Mercedes-Benz C-Class 2017','Nissan Qashqai 2020','Mazda CX-5 2019']
PARTS=[('Колодки тормозные','Brembo',7800,5100),('Масло и фильтр','MANN',6400,4300),('Амортизатор','KYB',14200,10100),('Комплект сцепления','LuK',26800,20800),('Радиатор','Denso',18900,13700),('Подшипник ступицы','SKF',9600,6800),('Комплект ГРМ','Gates',12400,8800),('Фара','Depo',17300,12600)]
PREFIX='+7999555'
def final_status(i):
 b=i%20
 return LeadStatus.NEW if b<3 else LeadStatus.IN_PROGRESS if b<6 else LeadStatus.SELECTION if b<9 else LeadStatus.INVOICE if b<12 else LeadStatus.WON if b<18 else LeadStatus.LOST
def path_for(final):
 p=[LeadStatus.NEW,LeadStatus.IN_PROGRESS,LeadStatus.SELECTION,LeadStatus.INVOICE]
 return [*p,final] if final in (LeadStatus.WON,LeadStatus.LOST) else p[:p.index(final)+1]
def durations(i,n):return [timedelta(minutes=x) for x in [30+i%151,90+(i*37)%630,150+(i*53)%1290,120+(i*71)%2760][:n]]
async def seed(count,dry=False):
 if not 50<=count<=70:raise SystemExit('--count должен быть от 50 до 70')
 async with get_session_factory()() as session:
  managers=list((await session.scalars(select(User).where(User.role==UserRole.MANAGER).order_by(User.id))).all())
  if not managers:managers=list((await session.scalars(select(User).where(User.role==UserRole.ADMIN).order_by(User.id))).all())
  if not managers:raise SystemExit('Сначала создайте пользователя')
  existing=int(await session.scalar(select(func.count(Lead.id)).where(Lead.phone.like(f'{PREFIX}%'))) or 0);missing=max(0,count-existing)
  print(f'[portfolio] уже есть: {existing}; будет добавлено: {missing}')
  if dry or not missing:return
  now=datetime.now(UTC).replace(second=0,microsecond=0)
  for i in range(existing,count):
   final=final_status(i);path=path_for(final);ds=durations(i,len(path)-1)
   finish=now-timedelta(days=(i*4)%88,hours=(i*3)%20)
   created=finish-sum(ds,timedelta()) if final in (LeadStatus.WON,LeadStatus.LOST) else now-timedelta(days=(i*7)%64,hours=(i*5)%20)
   manager=managers[i%len(managers)];selected=[] if final in (LeadStatus.NEW,LeadStatus.IN_PROGRESS) else [PARTS[i%len(PARTS)]]
   if selected and i%3==0:selected.append(PARTS[(i+3)%len(PARTS)])
   amount=sum(x[2] for x in selected);margin=sum(x[2]-x[3] for x in selected)
   lead=Lead(name=f'{FIRST[i%len(FIRST)]} {LAST[(i*3)%len(LAST)]}',phone=f'{PREFIX}{i:04d}',source=[LeadSource.TELEGRAM,LeadSource.MANUAL,LeadSource.SITE][i%3],vin=f'XTA{i:014d}'[:17],car_info=CARS[i%len(CARS)],status=final,manager_id=manager.id,created_at=created,updated_at=created,priority=['low','normal','high','urgent'][i%4],rejection_reason='Клиент отложил ремонт' if final==LeadStatus.LOST else None,total_amount=float(amount),total_margin=float(margin))
   session.add(lead);await session.flush();event=created
   session.add(StatusHistory(lead_id=lead.id,from_status=None,to_status='new',changed_by=manager.id,changed_at=event));session.add(AuditLog(lead_id=lead.id,actor_id=manager.id,action='lead_created',created_at=event))
   for n,target in enumerate(path[1:]):
    event+=ds[n];prev=path[n];session.add(StatusHistory(lead_id=lead.id,from_status=prev.value,to_status=target.value,changed_by=manager.id,changed_at=event));session.add(AuditLog(lead_id=lead.id,actor_id=manager.id,action='status_changed',field='status',old_value=prev.value,new_value=target.value,created_at=event))
   lead.updated_at=event
   for n,(name,brand,price,purchase) in enumerate(selected,1):session.add(OrderItem(lead_id=lead.id,oem=f'OEM-{i:03d}-{n}',brand=brand,name=name,price=price,purchase_price=purchase,qty=1,is_analog=n>1))
  await session.commit();total=int(await session.scalar(select(func.count(Lead.id))) or 0);print(f'[portfolio] готово: добавлено {missing}; всего заявок: {total}')
def main():
 p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=60);p.add_argument('--dry-run',action='store_true');a=p.parse_args();asyncio.run(seed(a.count,a.dry_run))
if __name__=='__main__':main()
