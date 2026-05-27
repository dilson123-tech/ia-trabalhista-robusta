from fastapi import APIRouter

from app.services.legal_modules import list_legal_modules

router = APIRouter(prefix="/legal-modules", tags=["legal-modules"])


@router.get("")
def get_legal_modules() -> list[dict]:
    return list_legal_modules()
