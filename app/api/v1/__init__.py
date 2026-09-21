from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.expenses import router as expenses_router
from app.api.v1.categories import router as categories_router
from app.api.v1.budgets import router as budgets_router
from app.api.v1.ai import router as ai_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.webhooks import router as webhooks_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(expenses_router)
api_router.include_router(categories_router)
api_router.include_router(budgets_router)
api_router.include_router(ai_router)
api_router.include_router(analytics_router)
api_router.include_router(webhooks_router)
