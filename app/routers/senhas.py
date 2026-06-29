from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session
from app.domain.services.senha_service import SenhaService
from app.schemas.senhas import GenerateSenhasRequest, GenerateSenhasResponse, SenhaRead

router = APIRouter()
service = SenhaService()


@router.get("/setor/{setor_id}", response_model=list[SenhaRead])
async def list_senhas_by_setor(
    setor_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[SenhaRead]:
    return await service.list_by_setor(session, setor_id)


@router.post("/gerar", response_model=GenerateSenhasResponse, status_code=status.HTTP_201_CREATED)
async def generate_senhas(
    payload: GenerateSenhasRequest,
    session: AsyncSession = Depends(get_session),
) -> GenerateSenhasResponse:
    return await service.generate(session, payload)


@router.delete("/{senha_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_senha(
    senha_id: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.delete(session, senha_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
