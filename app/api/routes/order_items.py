"""CRUD позиций заказа внутри заявки."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
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

router = APIRouter(prefix="/leads/{lead_id}/items", tags=["Позиции заказа"])

ADD_ITEM_EXAMPLES = {
    "Оригинальная позиция": {
        "summary": "Добавление оригинальной детали",
        "value": {
            "name": "Тормозной диск передний",
            "oem": "1K0615301AA",
            "brand": "ATE",
            "price": 5200,
            "purchase_price": 3800,
            "qty": 2,
            "is_analog": False,
        },
    },
    "Аналог": {
        "summary": "Добавление аналога",
        "value": {
            "name": "Тормозной диск передний (аналог)",
            "oem": "DF4451",
            "brand": "TRW",
            "price": 3900,
            "purchase_price": 2600,
            "qty": 2,
            "is_analog": True,
        },
    },
}

UPDATE_ITEM_EXAMPLES = {
    "Изменение позиции": {
        "summary": "Изменение цены и количества",
        "value": {"price": 4100, "qty": 3},
    }
}


def get_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrderItemService:
    return OrderItemService(session)


def lead_not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="Заявка не найдена")


def item_not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="Позиция заказа не найдена")


@router.post(
    "",
    response_model=OrderItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить позицию",
    description=(
        "Добавляет позицию (оригинал или аналог) в заявку. "
        "Признак аналога задаётся полем `is_analog`."
    ),
    responses={
        201: {"description": "Позиция добавлена"},
        401: {"description": "Не авторизован — требуется валидный токен"},
        404: {"description": "Заявка не найдена"},
        422: {"description": "Ошибка валидации данных позиции"},
    },
)
async def add_order_item(
    lead_id: int,
    data: Annotated[OrderItemCreate, Body(openapi_examples=ADD_ITEM_EXAMPLES)],
    service: Annotated[OrderItemService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> OrderItemRead:
    try:
        return await service.add(lead_id, data)
    except OrderItemLeadNotFoundError as error:
        raise lead_not_found() from error


@router.get(
    "",
    response_model=OrderItemsSummary,
    summary="Позиции заявки",
    description=(
        "Возвращает позиции заявки с разбивкой на оригиналы и аналоги "
        "и рассчитанными итогами."
    ),
    responses={
        200: {"description": "Список позиций и итоги"},
        401: {"description": "Не авторизован — требуется валидный токен"},
        404: {"description": "Заявка не найдена"},
    },
)
async def list_order_items(
    lead_id: int,
    service: Annotated[OrderItemService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> OrderItemsSummary:
    try:
        return await service.list(lead_id)
    except OrderItemLeadNotFoundError as error:
        raise lead_not_found() from error


@router.patch(
    "/{item_id}",
    response_model=OrderItemRead,
    summary="Изменить позицию",
    description="Частично обновляет поля позиции заказа.",
    responses={
        200: {"description": "Позиция обновлена"},
        401: {"description": "Не авторизован — требуется валидный токен"},
        404: {"description": "Заявка или позиция не найдена"},
        422: {"description": "Ошибка валидации данных позиции"},
    },
)
async def update_order_item(
    lead_id: int,
    item_id: int,
    data: Annotated[OrderItemUpdate, Body(openapi_examples=UPDATE_ITEM_EXAMPLES)],
    service: Annotated[OrderItemService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> OrderItemRead:
    try:
        return await service.update(lead_id, item_id, data)
    except OrderItemLeadNotFoundError as error:
        raise lead_not_found() from error
    except OrderItemNotFoundError as error:
        raise item_not_found() from error


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить позицию",
    description="Удаляет позицию заказа из заявки.",
    responses={
        204: {"description": "Позиция удалена, тело ответа отсутствует"},
        401: {"description": "Не авторизован — требуется валидный токен"},
        404: {"description": "Заявка или позиция не найдена"},
    },
)
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
