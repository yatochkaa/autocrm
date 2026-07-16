from fastapi import APIRouter

from app.api.routes import analytics, auth, health, leads, order_items

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(leads.router)
api_router.include_router(order_items.router)
api_router.include_router(analytics.router)
api_router.include_router(auth.router)
