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


@router.get("/export/tabs")
async def export_tabs(session: AsyncSession = Depends(get_session)) -> dict:
    return await service.export_tabs(session)


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(session: AsyncSession = Depends(get_session)) -> DashboardResponse:
    return await service.dashboard(session)


@router.get("/setor/{setor_id}/respondentes")
async def get_respondentes(
    setor_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await service.respondentes_por_setor(session, setor_id)


@router.get("/setor/{setor_id}/preferencias")
async def get_preferencias(
    setor_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await service.preferencias_por_setor(session, setor_id)


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


@router.get("/cultura/resultados")
async def get_cultura_resultados(
    setor_id: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await service.cultura_aggregate(session, setor_id)


@router.get("/respondentes/detalhado")
async def get_respondentes_detalhado(
    setor_id: int | None = None,
    page: int = 1,
    page_size: int = 10,
    busca: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await service.respondentes_detalhado(session, setor_id, page, page_size, busca)
