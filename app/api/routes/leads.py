"""CRUD и смена статуса заявок."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.database import get_session
from app.db.enums import LeadSource, LeadStatus
from app.db.models.user import User
from app.domain.funnel import InvalidTransition
from app.domain.lead_data import LeadDataError
from app.schemas.lead import LeadCreate, LeadRead, LeadStatusUpdate, LeadUpdate
from app.services.lead import LeadNotFoundError, LeadService

router = APIRouter(prefix="/leads", tags=["leads"])


def get_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LeadService:
    return LeadService(session)


def not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="Заявка не найдена")


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
async def create_lead(
    data: LeadCreate,
    service: Annotated[LeadService, Depends(get_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LeadRead:
    try:
        return await service.create(data, current_user)
    except LeadDataError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("", response_model=list[LeadRead])
async def list_leads(
    service: Annotated[LeadService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
    status_filter: Annotated[
        LeadStatus | None,
        Query(alias="status"),
    ] = None,
    source: LeadSource | None = None,
    manager_id: int | None = None,
) -> list[LeadRead]:
    return list(await service.list(status_filter, source, manager_id))


@router.get("/{lead_id}", response_model=LeadRead)
async def get_lead(
    lead_id: int,
    service: Annotated[LeadService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> LeadRead:
    try:
        return await service.get(lead_id)
    except LeadNotFoundError as error:
        raise not_found() from error


@router.patch("/{lead_id}", response_model=LeadRead)
async def update_lead(
    lead_id: int,
    data: LeadUpdate,
    service: Annotated[LeadService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> LeadRead:
    try:
        return await service.update(lead_id, data)
    except LeadNotFoundError as error:
        raise not_found() from error
    except LeadDataError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.patch("/{lead_id}/status", response_model=LeadRead)
async def change_lead_status(
    lead_id: int,
    data: LeadStatusUpdate,
    service: Annotated[LeadService, Depends(get_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LeadRead:
    try:
        return await service.change_status(lead_id, data.status, current_user)
    except LeadNotFoundError as error:
        raise not_found() from error
    except InvalidTransition as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: int,
    service: Annotated[LeadService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> Response:
    try:
        await service.delete(lead_id)
    except LeadNotFoundError as error:
        raise not_found() from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
