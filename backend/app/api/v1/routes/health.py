from fastapi import APIRouter
from app.core.settings import settings

router = APIRouter()

@router.get("/health", tags=["ops"])
def health_v1():
    return {"ok": True, "service": "ia_trabalhista_robusta", "env": settings.APP_ENV, "version": "0.1.0"}
