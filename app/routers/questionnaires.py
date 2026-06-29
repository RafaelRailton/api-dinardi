from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session
from app.domain.services.questionnaire_service import QuestionnaireService
from app.schemas.questions import PerguntaOpcaoRead, PerguntaPreferenciaRead
from app.schemas.responses import (
    FormularioSubmitResponse,
    OpcaoSubmitRequest,
    PreferenciaClassificacaoSubmitRequest,
    PreferenciaPesosSubmitRequest,
)

router = APIRouter()
service = QuestionnaireService()


@router.get("/opcoes/perguntas", response_model=list[PerguntaOpcaoRead])
async def list_opcoes(session: AsyncSession = Depends(get_session)) -> list[PerguntaOpcaoRead]:
    return await service.list_opcoes(session)


@router.get("/preferencias/perguntas", response_model=list[PerguntaPreferenciaRead])
async def list_preferencias(
    session: AsyncSession = Depends(get_session),
) -> list[PerguntaPreferenciaRead]:
    return await service.list_preferencias(session)


@router.post("/opcoes/respostas", response_model=FormularioSubmitResponse)
async def submit_opcoes(
    payload: OpcaoSubmitRequest,
    session: AsyncSession = Depends(get_session),
) -> FormularioSubmitResponse:
    return await service.submit_opcoes(session, payload)


@router.post("/preferencias/respostas", response_model=FormularioSubmitResponse)
async def submit_preference_weights(
    payload: PreferenciaPesosSubmitRequest,
    session: AsyncSession = Depends(get_session),
) -> FormularioSubmitResponse:
    return await service.submit_preference_weights(session, payload)


@router.post("/preferencias/classificacao", response_model=FormularioSubmitResponse)
async def submit_preference_classification(
    payload: PreferenciaClassificacaoSubmitRequest,
    session: AsyncSession = Depends(get_session),
) -> FormularioSubmitResponse:
    return await service.submit_preference_classification(session, payload)
