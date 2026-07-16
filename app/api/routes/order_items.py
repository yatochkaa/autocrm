"""CRUD позиций заказа внутри заявки."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.database import get_session
from app.db.models.user import User
from app.schemas.order_item import (
    OrderItemCreate,
    OrderItemRead,
    OrderItemsSummary,
    OrderItemUpdate,
)
from app.services.order_item import (
    OrderItemLeadNotFoundError,
    OrderItemNotFoundError,
    OrderItemService,
)

router = APIRouter(prefix="/leads/{lead_id}/items", tags=["order_items"])


def get_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrderItemService:
    return OrderItemService(session)


def lead_not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="Заявка не найдена")


def item_not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="Позиция заказа не найдена")


@router.post("", response_model=OrderItemRead, status_code=status.HTTP_201_CREATED)
async def add_order_item(
    lead_id: int,
    data: OrderItemCreate,
    service: Annotated[OrderItemService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> OrderItemRead:
    try:
        return await service.add(lead_id, data)
    except OrderItemLeadNotFoundError as error:
        raise lead_not_found() from error


@router.get("", response_model=OrderItemsSummary)
async def list_order_items(
    lead_id: int,
    service: Annotated[OrderItemService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> OrderItemsSummary:
    try:
        return await service.list(lead_id)
    except OrderItemLeadNotFoundError as error:
        raise lead_not_found() from error


@router.patch("/{item_id}", response_model=OrderItemRead)
async def update_order_item(
    lead_id: int,
    item_id: int,
    data: OrderItemUpdate,
    service: Annotated[OrderItemService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> OrderItemRead:
    try:
        return await service.update(lead_id, item_id, data)
    except OrderItemLeadNotFoundError as error:
        raise lead_not_found() from error
    except OrderItemNotFoundError as error:
        raise item_not_found() from error


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order_item(
    lead_id: int,
    item_id: int,
    service: Annotated[OrderItemService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> Response:
    try:
        await service.delete(lead_id, item_id)
    except OrderItemLeadNotFoundError as error:
        raise lead_not_found() from error
    except OrderItemNotFoundError as error:
        raise item_not_found() from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
