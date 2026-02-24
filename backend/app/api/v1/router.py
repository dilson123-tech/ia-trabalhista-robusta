from fastapi import APIRouter

from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.cases import router as cases_router
from app.api.v1.routes.usage import router as usage_router
from app.api.v1.routes.admin import router as admin_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(cases_router)
api_router.include_router(usage_router)

# admin
api_router.include_router(admin_router)
