from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session
from app.domain.services.auth_service import AuthService
from app.schemas.auth import (
    AdminLoginRequest,
    AdminSession,
    RespondentLoginRequest,
    RespondentSession,
)

router = APIRouter()
service = AuthService()


@router.post("/respondente/login", response_model=RespondentSession)
async def login_respondente(
    payload: RespondentLoginRequest,
    session: AsyncSession = Depends(get_session),
) -> RespondentSession:
    return await service.login_respondent(session, payload)


@router.get("/respondente/{senha_id}/status", response_model=RespondentSession)
async def get_respondente_status(
    senha_id: int,
    session: AsyncSession = Depends(get_session),
) -> RespondentSession:
    return await service.get_respondent_status(session, senha_id)


@router.post("/admin/login", response_model=AdminSession)
async def login_admin(payload: AdminLoginRequest) -> AdminSession:
    return await service.login_admin(payload)
