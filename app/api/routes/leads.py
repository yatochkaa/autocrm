"""CRUD, пагинация и смена статуса заявок."""

from __future__ import annotations

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies.auth import get_current_user
from app.core.database import get_session
from app.db.enums import LeadPriority, LeadSource, LeadStatus, UserRole
from app.db.models.lead import Lead
from app.db.models.user import User
from app.domain.funnel import InvalidTransition
from app.domain.lead_data import LeadDataError
from app.schemas.audit_log import AuditLogOut
from app.schemas.lead import (
    LeadCreate,
    LeadRead,
    LeadStatusUpdate,
    LeadUpdate,
    PaginatedLeads,
)
from app.schemas.status_history import StatusHistoryRead
from app.services.lead import LeadNotFoundError, LeadService

router = APIRouter(prefix="/leads", tags=["leads"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_service(session: SessionDep) -> LeadService:
    return LeadService(session)


ServiceDep = Annotated[LeadService, Depends(get_service)]


def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Только для администратора")
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]


def not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="Заявка не найдена")


def ensure_access(lead: Lead, current_user: User) -> None:
    if (
        current_user.role == UserRole.MANAGER
        and lead.manager_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Нет доступа к заявке")


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
async def create_lead(
    data: LeadCreate,
    service: ServiceDep,
    current_user: CurrentUser,
) -> LeadRead:
    try:
        return await service.create(data, current_user)
    except LeadDataError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("", response_model=list[LeadRead] | PaginatedLeads)
async def list_leads(
    session: SessionDep,
    current_user: CurrentUser,
    status_filter: Annotated[LeadStatus | None, Query(alias="status")] = None,
    source: LeadSource | None = None,
    manager_id: int | None = None,
    priority: LeadPriority | None = None,
    search: str | None = None,
    include_completed: bool | None = None,
    page: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int | None, Query(ge=1, le=200)] = None,
    sort: str | None = None,
    order: str | None = None,
) -> list[Lead] | PaginatedLeads:
    statement = select(Lead).options(
        selectinload(Lead.items),
        selectinload(Lead.history),
    )

    if current_user.role == UserRole.MANAGER:
        statement = statement.where(Lead.manager_id == current_user.id)
    elif manager_id is not None:
        statement = statement.where(Lead.manager_id == manager_id)

    if status_filter is not None:
        statement = statement.where(Lead.status == status_filter)
    elif include_completed is False:
        statement = statement.where(
            Lead.status.notin_([LeadStatus.WON, LeadStatus.LOST])
        )
    if source is not None:
        statement = statement.where(Lead.source == source)
    if priority is not None:
        statement = statement.where(Lead.priority == priority.value)
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Lead.name.ilike(pattern),
                Lead.phone.ilike(pattern),
                Lead.vin.ilike(pattern),
                Lead.car_info.ilike(pattern),
            )
        )

    legacy_response = (
        page is None
        and limit is None
        and priority is None
        and search is None
        and include_completed is None
        and sort is None
        and order is None
    )
    if legacy_response:
        statement = statement.order_by(Lead.created_at.desc(), Lead.id.desc())
        rows = (await session.scalars(statement)).all()
        return list(rows)

    actual_page = page or 1
    actual_limit = limit or 20
    total = await session.scalar(
        select(func.count()).select_from(statement.order_by(None).subquery())
    )

    allowed_sort = {
        "created_at": Lead.created_at,
        "updated_at": Lead.updated_at,
        "priority": Lead.priority,
        "status": Lead.status,
        "name": Lead.name,
        "total_amount": Lead.total_amount,
    }
    sort_column = allowed_sort.get(sort or "created_at", Lead.created_at)
    statement = statement.order_by(
        sort_column.asc() if order == "asc" else sort_column.desc(),
        Lead.id.desc(),
    )
    statement = statement.offset((actual_page - 1) * actual_limit).limit(
        actual_limit
    )
    rows = (await session.scalars(statement)).all()
    total_value = int(total or 0)
    return PaginatedLeads(
        items=[LeadRead.model_validate(row) for row in rows],
        total=total_value,
        page=actual_page,
        limit=actual_limit,
        pages=max(1, math.ceil(total_value / actual_limit)),
    )


@router.get("/{lead_id}", response_model=LeadRead)
async def get_lead(
    lead_id: int,
    service: ServiceDep,
    current_user: CurrentUser,
) -> LeadRead:
    try:
        lead = await service.get(lead_id)
    except LeadNotFoundError as error:
        raise not_found() from error
    ensure_access(lead, current_user)
    return lead


@router.patch("/{lead_id}", response_model=LeadRead)
async def update_lead(
    lead_id: int,
    data: LeadUpdate,
    service: ServiceDep,
    current_user: CurrentUser,
) -> LeadRead:
    try:
        lead = await service.get(lead_id)
        ensure_access(lead, current_user)
        return await service.update(lead_id, data, current_user.id)
    except LeadNotFoundError as error:
        raise not_found() from error
    except LeadDataError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.patch("/{lead_id}/status", response_model=LeadRead)
async def change_lead_status(
    lead_id: int,
    data: LeadStatusUpdate,
    service: ServiceDep,
    current_user: CurrentUser,
) -> LeadRead:
    try:
        lead = await service.get(lead_id)
        ensure_access(lead, current_user)
        return await service.change_status(
            lead_id,
            data.status,
            current_user,
            data.rejection_reason,
        )
    except LeadNotFoundError as error:
        raise not_found() from error
    except InvalidTransition as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except LeadDataError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.delete(
    "/{lead_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_lead(
    lead_id: int,
    service: ServiceDep,
    _admin: AdminUser,
) -> Response:
    try:
        await service.delete(lead_id)
    except LeadNotFoundError as error:
        raise not_found() from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{lead_id}/history", response_model=list[StatusHistoryRead])
async def get_history(
    lead_id: int,
    service: ServiceDep,
    current_user: CurrentUser,
) -> list[StatusHistoryRead]:
    try:
        lead = await service.get(lead_id)
    except LeadNotFoundError as error:
        raise not_found() from error
    ensure_access(lead, current_user)
    return lead.history


@router.get("/{lead_id}/audit", response_model=list[AuditLogOut])
async def get_audit(
    lead_id: int,
    service: ServiceDep,
    _admin: AdminUser,
) -> list[AuditLogOut]:
    try:
        lead = await service.get(lead_id)
    except LeadNotFoundError as error:
        raise not_found() from error
    return lead.audit_logs
