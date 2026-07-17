from fastapi import APIRouter

from app.api.routes import analytics, auth, comments, health, leads, order_items, settings

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(leads.router)
api_router.include_router(comments.router)
api_router.include_router(order_items.router)
api_router.include_router(analytics.router)
api_router.include_router(auth.router)

api_router.include_router(settings.router)
