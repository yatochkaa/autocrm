from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.domain.enums import LeadStatus
from app.domain.funnel import FunnelError
from app.schemas.lead import LeadCreate, LeadRead, LeadStatusUpdate, LeadUpdate
from app.services.lead import LeadService

router = APIRouter(prefix="/leads", tags=["leads"])


def get_service(session: AsyncSession = Depends(get_session)) -> LeadService:
    """Фабрика сервиса заявок на основе сессии БД."""
    return LeadService(session)


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
async def create_lead(
    data: LeadCreate,
    service: LeadService = Depends(get_service),
):
    """Создать новую заявку."""
    return await service.create(data)


@router.get("", response_model=list[LeadRead])
async def list_leads(
    status_filter: LeadStatus | None = Query(default=None, alias="status"),
    service: LeadService = Depends(get_service),
):
    """Список заявок, опционально фильтр ?status=..."""
    return await service.list(status_filter)


@router.get("/{lead_id}", response_model=LeadRead)
async def get_lead(
    lead_id: int,
    service: LeadService = Depends(get_service),
):
    """Получить заявку по id."""
    lead = await service.get(lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
    return lead


@router.patch("/{lead_id}", response_model=LeadRead)
async def update_lead(
    lead_id: int,
    data: LeadUpdate,
    service: LeadService = Depends(get_service),
):
    """Частично обновить заявку."""
    lead = await service.update(lead_id, data)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
    return lead


@router.post("/{lead_id}/status", response_model=LeadRead)
async def change_lead_status(
    lead_id: int,
    data: LeadStatusUpdate,
    service: LeadService = Depends(get_service),
):
    """Сменить стадию воронки (с проверкой допустимости перехода)."""
    try:
        lead = await service.change_status(lead_id, data.status)
    except FunnelError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: int,
    service: LeadService = Depends(get_service),
) -> None:
    """Удалить заявку."""
    ok = await service.delete(lead_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
