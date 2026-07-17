"""app/api/routes/leads.py  — FULL REPLACEMENT (Phase 2).

Changes vs original:
  + Пагинация: GET /leads → PaginatedLeads
  + Фильтры: priority, search, include_completed, sort/order
  + Разграничение: admin — всё, manager — только свои
  + DELETE: только admin
  + GET /{id}/history, GET /{id}/audit
  + rejection_reason обязателен при status=lost
  + AuditLog запись при update / status_change
  ИТЕМЫ НЕ ДУБЛИРОВАНЫ — они живут в order_items.py
"""

# ruff: noqa: B008
from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies.auth import get_current_user
from app.core.database import get_session
from app.db.enums import UserRole
from app.db.models import AuditLog, Lead, StatusHistory
from app.db.models.user import User
from app.schemas.audit_log import AuditLogOut
from app.schemas.lead import (
    LeadCreate,
    LeadOut,
    LeadStatusHistoryOut,
    LeadStatusUpdate,
    LeadUpdate,
    PaginatedLeads,
)

router = APIRouter(prefix="/leads", tags=["leads"])

ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "new": ["in_progress"],
    "in_progress": ["selection"],
    "selection": ["invoice"],
    "invoice": ["won", "lost"],
}


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """403 если не admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user


async def _get_lead_or_404(
    lead_id: int,
    session: AsyncSession,
    current_user: User | None = None,
) -> Lead:
    stmt = (
        select(Lead)
        .where(Lead.id == lead_id)
        .options(
            selectinload(Lead.items),
            selectinload(Lead.history),
            selectinload(Lead.audit_logs),
        )
    )
    lead = (await session.execute(stmt)).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if (
        current_user
        and current_user.role == UserRole.MANAGER
        and lead.manager_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    return lead


def _recalc(lead: Lead) -> None:
    """Пересчитать сумму и маржу заявки."""
    amount = 0.0
    margin = 0.0
    for item in lead.items:
        qty = item.qty or 1
        price = item.price or 0.0
        purchase = item.purchase_price or 0.0
        amount += qty * price
        margin += qty * (price - purchase)
    lead.total_amount = amount
    lead.total_margin = margin


@router.get("", response_model=PaginatedLeads)
async def list_leads(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    status_filter: str | None = Query(None, alias="status"),
    source: str | None = Query(None),
    priority: str | None = Query(None),
    manager_id: int | None = Query(None),
    search: str | None = Query(None),
    include_completed: bool = Query(False),
    sort: str = Query("created_at"),
    order: str = Query("desc"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PaginatedLeads:
    stmt = select(Lead).options(
        selectinload(Lead.items),
        selectinload(Lead.history),
    )
    # Разграничение доступа
    if current_user.role == UserRole.MANAGER:
        stmt = stmt.where(Lead.manager_id == current_user.id)
    elif manager_id is not None:
        stmt = stmt.where(Lead.manager_id == manager_id)

    if status_filter:
        stmt = stmt.where(Lead.status == status_filter)
    elif not include_completed:
        stmt = stmt.where(Lead.status.notin_(["won", "lost"]))

    if source:
        stmt = stmt.where(Lead.source == source)
    if priority:
        stmt = stmt.where(Lead.priority == priority)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            or_(
                Lead.name.ilike(like),
                Lead.phone.ilike(like),
                Lead.vin.ilike(like),
            )
        )

    total: int = (
        await session.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()

    allowed_sort = {
        "created_at",
        "updated_at",
        "priority",
        "status",
        "name",
        "total_amount",
    }
    col = getattr(Lead, sort if sort in allowed_sort else "created_at")
    stmt = stmt.order_by(col.desc() if order == "desc" else col.asc())
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()

    return PaginatedLeads(
        items=[LeadOut.model_validate(r) for r in rows],
        total=total,
        page=page,
        limit=limit,
        pages=max(1, math.ceil(total / limit)),
    )


@router.post("", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
async def create_lead(
    body: LeadCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LeadOut:
    data = body.model_dump()
    if current_user.role == UserRole.MANAGER:
        data["manager_id"] = current_user.id
    lead = Lead(**data)
    session.add(lead)
    await session.flush()
    session.add(
        StatusHistory(
            lead_id=lead.id,
            from_status=None,
            to_status=lead.status,
            changed_by=current_user.id,
        )
    )
    await session.commit()
    return await _get_lead_or_404(lead.id, session, current_user)


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(
    lead_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LeadOut:
    return await _get_lead_or_404(lead_id, session, current_user)


@router.patch("/{lead_id}", response_model=LeadOut)
async def update_lead(
    lead_id: int,
    body: LeadUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LeadOut:
    lead = await _get_lead_or_404(lead_id, session, current_user)
    updates = body.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(lead, k, v)
    session.add(
        AuditLog(
            lead_id=lead.id,
            actor_id=current_user.id,
            action="update",
            meta=str(list(updates.keys())),
        )
    )
    await session.commit()
    return await _get_lead_or_404(lead_id, session, current_user)


@router.patch("/{lead_id}/status", response_model=LeadOut)
async def change_status(
    lead_id: int,
    body: LeadStatusUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LeadOut:
    lead = await _get_lead_or_404(lead_id, session, current_user)
    allowed = ALLOWED_TRANSITIONS.get(lead.status, [])
    if body.status not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Transition {lead.status!r} -> {body.status!r} not allowed",
        )
    if body.status == "lost" and not body.rejection_reason:
        raise HTTPException(
            status_code=422, detail="rejection_reason required when status=lost"
        )
    old = lead.status
    lead.status = body.status
    if body.rejection_reason is not None:
        lead.rejection_reason = body.rejection_reason
    session.add(
        StatusHistory(
            lead_id=lead.id,
            from_status=old,
            to_status=body.status,
            changed_by=current_user.id,
        )
    )
    session.add(
        AuditLog(
            lead_id=lead.id,
            actor_id=current_user.id,
            action="status_change",
            field="status",
            old_value=old,
            new_value=body.status,
        )
    )
    await session.commit()
    return await _get_lead_or_404(lead_id, session, current_user)


@router.delete(
    "/{lead_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_lead(
    lead_id: int,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_admin),
) -> Response:
    lead = await session.get(Lead, lead_id)

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    await session.delete(lead)
    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{lead_id}/history", response_model=list[LeadStatusHistoryOut])
async def get_history(
    lead_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[LeadStatusHistoryOut]:
    lead = await _get_lead_or_404(lead_id, session, current_user)
    return lead.history


@router.get("/{lead_id}/audit", response_model=list[AuditLogOut])
async def get_audit(
    lead_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[AuditLogOut]:
    lead = await _get_lead_or_404(lead_id, session, current_user)
    return lead.audit_logs
