from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session
from app.domain.services.questionnaire_service import QuestionnaireService
from app.schemas.questions import PerguntaCulturaRead, PerguntaOpcaoRead, PerguntaPreferenciaRead
from app.schemas.responses import (
    CulturaRespostaSalva,
    CulturaResultadoResponse,
    CulturaSalvarRequest,
    CulturaSubmitRequest,
    CulturaSubmitResponse,
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


@router.get("/cultura/perguntas", response_model=list[PerguntaCulturaRead])
async def list_cultura(session: AsyncSession = Depends(get_session)) -> list[PerguntaCulturaRead]:
    return await service.list_cultura(session)


@router.get("/cultura/respostas/{senha_id}", response_model=list[CulturaRespostaSalva])
async def get_cultura_respostas(
    senha_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[CulturaRespostaSalva]:
    return await service.get_cultura_respostas(session, senha_id)


@router.post("/cultura/respostas/salvar")
async def salvar_resposta_cultura(
    payload: CulturaSalvarRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    await service._ensure_senha_belongs_to_setor(session, payload.senha_id, payload.setor_id)
    await service.salvar_resposta_cultura(
        session, payload.senha_id, payload.setor_id, payload.pergunta_id, payload.resposta
    )
    return {"ok": True}


@router.post("/cultura/respostas", response_model=CulturaSubmitResponse)
async def submit_cultura(
    payload: CulturaSubmitRequest,
    session: AsyncSession = Depends(get_session),
) -> CulturaSubmitResponse:
    return await service.submit_cultura(session, payload)


@router.get("/cultura/resultado/{senha_id}", response_model=CulturaResultadoResponse)
async def get_cultura_resultado(
    senha_id: int,
    session: AsyncSession = Depends(get_session),
) -> CulturaResultadoResponse:
    return await service.calculate_cultura_result(session, senha_id)
