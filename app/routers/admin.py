from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session
from app.domain.services.admin_service import AdminService
from app.schemas.admin import CriarUsuarioRequest, DashboardResponse, ExportRow

router = APIRouter()
service = AdminService()


@router.get("/export/respostas", response_model=list[ExportRow])
async def export_respostas(session: AsyncSession = Depends(get_session)) -> list[ExportRow]:
    return await service.export_rows(session)


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(session: AsyncSession = Depends(get_session)) -> DashboardResponse:
    return await service.dashboard(session)


@router.get("/setor/{setor_id}/respondentes")
async def get_respondentes(
    setor_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await service.respondentes_por_setor(session, setor_id)


@router.post("/usuarios")
async def criar_usuario(
    payload: CriarUsuarioRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    usuario = await service.criar_usuario(session, payload)
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "cpf": usuario.cpf,
        "setor_id": usuario.setor_id,
    }
