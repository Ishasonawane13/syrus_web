"""API routers package."""
from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.account import router as account_router
from app.api.market import router as market_router
from app.api.orders import router as orders_router
from app.api.ai import router as ai_router
from app.api.audit import router as audit_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(account_router)
api_router.include_router(market_router)
api_router.include_router(orders_router)
api_router.include_router(ai_router)
api_router.include_router(audit_router)

__all__ = ["api_router"]
