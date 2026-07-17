"""CRUD и смена статуса заявок."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.database import get_session
from app.db.enums import LeadSource, LeadStatus
from app.db.models.user import User
from app.domain.funnel import InvalidTransition
from app.domain.lead_data import LeadDataError
from app.schemas.lead import LeadCreate, LeadRead, LeadStatusUpdate, LeadUpdate
from app.services.lead import LeadNotFoundError, LeadService

router = APIRouter(prefix="/leads", tags=["Заявки"])

CREATE_LEAD_EXAMPLES = {
    "Создание заявки": {
        "summary": "Новая заявка с одной позицией",
        "value": {
            "name": "Иван Петров",
            "phone": "+7 900 123-45-67",
            "source": "site",
            "vin": "WVWZZZ1KZAW000001",
            "car_info": "Volkswagen Golf 2019, 1.4 TSI",
            "manager_id": 1,
            "items": [
                {
                    "name": "Тормозные колодки передние",
                    "oem": "1K0698151",
                    "brand": "Bosch",
                    "price": 4500,
                    "purchase_price": 3200,
                    "qty": 1,
                    "is_analog": False,
                }
            ],
        },
    }
}

UPDATE_LEAD_EXAMPLES = {
    "Обновление заявки": {
        "summary": "Изменение контактов и менеджера",
        "value": {
            "name": "Иван Петров",
            "phone": "+7 900 765-43-21",
            "manager_id": 2,
        },
    }
}

STATUS_UPDATE_EXAMPLES = {
    "Смена статуса": {
        "summary": "Перевод заявки на следующий этап",
        "value": {"status": "in_progress"},
    }
}


def get_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LeadService:
    return LeadService(session)


def not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="Заявка не найдена")


@router.post(
    "",
    response_model=LeadRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать заявку",
    description=(
        "Создаёт новую заявку. Можно сразу передать список позиций " "в поле `items`."
    ),
    responses={
        201: {"description": "Заявка создана"},
        401: {"description": "Не авторизован — требуется валидный токен"},
        422: {"description": "Ошибка валидации данных заявки или позиций"},
    },
)
async def create_lead(
    data: Annotated[LeadCreate, Body(openapi_examples=CREATE_LEAD_EXAMPLES)],
    service: Annotated[LeadService, Depends(get_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LeadRead:
    try:
        return await service.create(data, current_user)
    except LeadDataError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get(
    "",
    response_model=list[LeadRead],
    summary="Список заявок",
    description=(
        "Возвращает список заявок с необязательными фильтрами по статусу, "
        "источнику и ответственному менеджеру."
    ),
    responses={
        200: {"description": "Список заявок"},
        401: {"description": "Не авторизован — требуется валидный токен"},
    },
)
async def list_leads(
    service: Annotated[LeadService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
    status_filter: Annotated[
        LeadStatus | None,
        Query(alias="status", description="Фильтр по статусу воронки"),
    ] = None,
    source: Annotated[
        LeadSource | None,
        Query(description="Фильтр по источнику заявки"),
    ] = None,
    manager_id: Annotated[
        int | None,
        Query(description="Фильтр по ID ответственного менеджера"),
    ] = None,
) -> list[LeadRead]:
    return list(await service.list(status_filter, source, manager_id))


@router.get(
    "/{lead_id}",
    response_model=LeadRead,
    summary="Получить заявку",
    description="Возвращает заявку по ID со всеми позициями и историей.",
    responses={
        200: {"description": "Данные заявки"},
        401: {"description": "Не авторизован — требуется валидный токен"},
        404: {"description": "Заявка не найдена"},
    },
)
async def get_lead(
    lead_id: int,
    service: Annotated[LeadService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> LeadRead:
    try:
        return await service.get(lead_id)
    except LeadNotFoundError as error:
        raise not_found() from error


@router.patch(
    "/{lead_id}",
    response_model=LeadRead,
    summary="Обновить заявку",
    description="Частично обновляет поля заявки. Передаются только нужные поля.",
    responses={
        200: {"description": "Заявка обновлена"},
        401: {"description": "Не авторизован — требуется валидный токен"},
        404: {"description": "Заявка не найдена"},
        422: {"description": "Ошибка валидации данных заявки"},
    },
)
async def update_lead(
    lead_id: int,
    data: Annotated[LeadUpdate, Body(openapi_examples=UPDATE_LEAD_EXAMPLES)],
    service: Annotated[LeadService, Depends(get_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> LeadRead:
    try:
        return await service.update(lead_id, data)
    except LeadNotFoundError as error:
        raise not_found() from error
    except LeadDataError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.patch(
    "/{lead_id}/status",
    response_model=LeadRead,
    summary="Сменить статус заявки",
    description=(
        "Меняет статус заявки по воронке продаж.\n\n"
        "Допустимая цепочка переходов:\n\n"
        "`new → in_progress → selection → invoice → won/lost`\n\n"
        "Переход не по цепочке возвращает ошибку 409."
    ),
    responses={
        200: {"description": "Статус изменён"},
        401: {"description": "Не авторизован — требуется валидный токен"},
        404: {"description": "Заявка не найдена"},
        409: {"description": "Недопустимый переход статуса по воронке"},
    },
)
async def change_lead_status(
    lead_id: int,
    data: Annotated[LeadStatusUpdate, Body(openapi_examples=STATUS_UPDATE_EXAMPLES)],
    service: Annotated[LeadService, Depends(get_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LeadRead:
    try:
        return await service.change_status(lead_id, data.status, current_user)
    except LeadNotFoundError as error:
        raise not_found() from error
    except InvalidTransition as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.delete(
    "/{lead_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить заявку",
    description="Удаляет заявку вместе со связанными позициями заказа.",
    responses={
        204: {"description": "Заявка удалена, тело ответа отсутствует"},
        401: {"description": "Не авторизован — требуется валидный токен"},
        404: {"description": "Заявка не найдена"},
    },
)
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
