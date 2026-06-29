from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session
from app.domain.services.setor_service import SetorService
from app.schemas.setores import SetorCreate, SetorRead, SetorSummary, SetorUpdate

router = APIRouter()
service = SetorService()


@router.get("", response_model=list[SetorSummary])
async def list_setores(session: AsyncSession = Depends(get_session)) -> list[SetorSummary]:
    return await service.list_setores(session)


@router.post("", response_model=SetorRead, status_code=status.HTTP_201_CREATED)
async def create_setor(
    payload: SetorCreate,
    session: AsyncSession = Depends(get_session),
) -> SetorRead:
    return await service.create_setor(session, payload)


@router.put("/{setor_id}", response_model=SetorRead)
async def update_setor(
    setor_id: int,
    payload: SetorUpdate,
    session: AsyncSession = Depends(get_session),
) -> SetorRead:
    return await service.update_setor(session, setor_id, payload)


@router.delete("/{setor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setor(
    setor_id: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.delete_setor(session, setor_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
