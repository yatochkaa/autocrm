"""CRUD, пагинация и смена статуса заявок."""

from __future__ import annotations

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies.auth import get_current_user
from app.core.database import get_session
from app.core.runtime_settings import refresh_auto_priorities
from app.core.user_profiles import profile_for
from app.db.enums import LeadPriority, LeadSource, LeadStatus, UserRole
from app.db.models.lead import Lead
from app.db.models.user import User
from app.domain.funnel import InvalidTransition
from app.domain.lead_data import LeadDataError
from app.schemas.audit_log import AuditLogOut
from app.schemas.lead import LeadCreate, LeadRead, LeadStatusUpdate, LeadUpdate
from app.schemas.lead import PaginatedLeads
from app.schemas.status_history import StatusHistoryRead
from app.services.excel_export import build_xlsx
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
    # Все авторизованные менеджеры видят и ведут все заявки.
    # Ответственный используется для аналитики, но не ограничивает видимость.
    return None


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
async def create_lead(
    data: LeadCreate,
    service: ServiceDep,
    current_user: CurrentUser,
) -> LeadRead:
    if current_user.role == UserRole.MANAGER:
        data = data.model_copy(update={"manager_id": current_user.id})
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
    await refresh_auto_priorities(session)
    statement = select(Lead).options(
        selectinload(Lead.items),
        selectinload(Lead.history),
    )

    if manager_id is not None and current_user.role == UserRole.ADMIN:
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

    priority_rank = case(
        (Lead.priority == "urgent", 4),
        (Lead.priority == "high", 3),
        (Lead.priority == "normal", 2),
        else_=1,
    )
    allowed_sort = {
        "created_at": Lead.created_at,
        "updated_at": Lead.updated_at,
        "priority": priority_rank,
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


@router.get("/export.xlsx")
async def export_leads_excel(
    session: SessionDep,
    current_user: CurrentUser,
    status_filter: Annotated[LeadStatus | None, Query(alias="status")] = None,
    source: LeadSource | None = None,
    manager_id: int | None = None,
    priority: LeadPriority | None = None,
    search: str | None = None,
    include_completed: bool = False,
) -> Response:
    await refresh_auto_priorities(session)
    statement = select(Lead)
    if manager_id is not None and current_user.role == UserRole.ADMIN:
        statement = statement.where(Lead.manager_id == manager_id)
    if status_filter is not None:
        statement = statement.where(Lead.status == status_filter)
    elif not include_completed:
        statement = statement.where(Lead.status.notin_([LeadStatus.WON, LeadStatus.LOST]))
    if source is not None:
        statement = statement.where(Lead.source == source)
    if priority is not None:
        statement = statement.where(Lead.priority == priority.value)
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(or_(Lead.name.ilike(pattern), Lead.phone.ilike(pattern), Lead.vin.ilike(pattern), Lead.car_info.ilike(pattern)))
    leads = list((await session.scalars(statement.order_by(Lead.created_at.desc(), Lead.id.desc()))).all())
    users = {user.id: user for user in (await session.scalars(select(User))).all()}
    status_labels = {"new":"Новая","in_progress":"В работе","selection":"Подбор","invoice":"Счёт","won":"Продажа","lost":"Отказ"}
    priority_labels = {"low":"Низкий","normal":"Обычный","high":"Высокий","urgent":"Срочный"}
    source_labels = {"telegram":"Telegram","manual":"Вручную","site":"Сайт"}
    rows = [["ID","Клиент","Телефон","Автомобиль","VIN","Статус","Приоритет","Источник","Ответственный","Сумма","Маржа","Причина отказа","Создана"]]
    for lead in leads:
        manager = users.get(lead.manager_id)
        manager_name = "Не назначен"
        if manager:
            manager_name = profile_for(manager.id, manager.email, manager.role.value).full_name
        status_value = lead.status.value if hasattr(lead.status, "value") else str(lead.status)
        source_value = lead.source.value if hasattr(lead.source, "value") else str(lead.source)
        rows.append([lead.id, lead.name, lead.phone or "", lead.car_info or "", lead.vin or "", status_labels.get(status_value,status_value), priority_labels.get(lead.priority,lead.priority), source_labels.get(source_value,source_value), manager_name, lead.total_amount or 0, lead.total_margin or 0, lead.rejection_reason or "", lead.created_at.astimezone().strftime("%d.%m.%Y %H:%M")])
    content = build_xlsx(rows, sheet_name="Заявки", header_rows={1}, widths=[8,24,18,26,20,14,14,14,24,14,14,28,20])
    return Response(content=content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition":"attachment; filename=autocrm-leads.xlsx"})


@router.get("/{lead_id}", response_model=LeadRead)
async def get_lead(
    lead_id: int,
    service: ServiceDep,
    current_user: CurrentUser,
) -> LeadRead:
    try:
        await refresh_auto_priorities(service.session, lead_id)
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
        if (
            current_user.role == UserRole.MANAGER
            and data.manager_id is not None
            and data.manager_id != current_user.id
        ):
            raise HTTPException(status_code=403, detail="Нельзя назначить заявку другому менеджеру")
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
