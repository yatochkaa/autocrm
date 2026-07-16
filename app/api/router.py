from fastapi import APIRouter

from app.api.routes import health, leads

# Корневой роутер API: сюда подключаются все модули маршрутов.
api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(leads.router)
