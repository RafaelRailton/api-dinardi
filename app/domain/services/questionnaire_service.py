from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import (
    PerguntaOpcao,
    PerguntaPreferencia,
    RespostaOpcao,
    RespostaPreferencia,
    Senha,
)
from app.schemas.questions import PerguntaOpcaoRead, PerguntaPreferenciaRead
from app.schemas.responses import (
    FormularioSubmitResponse,
    OpcaoSubmitRequest,
    PreferenciaClassificacaoSubmitRequest,
    PreferenciaPesoInput,
    PreferenciaPesosSubmitRequest,
)


class QuestionnaireService:
    async def list_opcoes(self, session: AsyncSession) -> list[PerguntaOpcaoRead]:
        rows = (
            await session.execute(select(PerguntaOpcao).order_by(PerguntaOpcao.ordem))
        ).scalars().all()
        return [
            PerguntaOpcaoRead(
                id=row.id,
                categoria=row.categoria,
                pergunta=row.pergunta,
                tipo=row.tipo,
                opcoes=row.opcoes,
                ordem=row.ordem,
            )
            for row in rows
        ]

    async def list_preferencias(self, session: AsyncSession) -> list[PerguntaPreferenciaRead]:
        rows = (
            await session.execute(select(PerguntaPreferencia).order_by(PerguntaPreferencia.ordem))
        ).scalars().all()
        return [
            PerguntaPreferenciaRead(
                id=row.id,
                categoria=row.categoria,
                pergunta=row.pergunta,
                tipo=row.tipo,
                opcoes=row.opcoes,
                peso=row.peso,
                ordem=row.ordem,
            )
            for row in rows
        ]

    async def submit_opcoes(
        self,
        session: AsyncSession,
        payload: OpcaoSubmitRequest,
    ) -> FormularioSubmitResponse:
        await self._ensure_senha_belongs_to_setor(session, payload.senha_id, payload.setor_id)
        pergunta_ids = await self._get_question_ids(session, PerguntaOpcao)
        received_ids = {item.pergunta_id for item in payload.respostas}
        self._ensure_known_questions(received_ids, pergunta_ids)

        now = datetime.now(timezone.utc)
        rows = [
            {
                "senha_id": payload.senha_id,
                "setor_id": payload.setor_id,
                "pergunta_id": item.pergunta_id,
                "resposta": item.resposta,
                "data_resposta": item.data_resposta or now,
            }
            for item in payload.respostas
        ]

        stmt = insert(RespostaOpcao).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["senha_id", "pergunta_id"],
            set_={
                "setor_id": stmt.excluded.setor_id,
                "resposta": stmt.excluded.resposta,
                "data_resposta": stmt.excluded.data_resposta,
            },
        )
        await session.execute(stmt)

        saved_count = await self._count_saved_answers(session, RespostaOpcao, payload.senha_id)
        if saved_count < len(pergunta_ids):
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formulario de opcoes incompleto",
            )

        await session.execute(
            update(Senha)
            .where(Senha.id == payload.senha_id)
            .values(
                formulario_opcoes_concluido=True,
                formulario_opcoes_concluido_em=now,
            )
        )
        await session.commit()

        return FormularioSubmitResponse(
            senha_id=payload.senha_id,
            formulario="opcoes",
            total_respostas=saved_count,
            concluido=True,
        )

    async def submit_preference_weights(
        self,
        session: AsyncSession,
        payload: PreferenciaPesosSubmitRequest,
    ) -> FormularioSubmitResponse:
        await self._ensure_senha_belongs_to_setor(session, payload.senha_id, payload.setor_id)
        pergunta_ids = await self._get_question_ids(session, PerguntaPreferencia)
        received_ids = {item.pergunta_id for item in payload.respostas}
        self._ensure_known_questions(received_ids, pergunta_ids)
        if received_ids != pergunta_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formulario de preferencias incompleto",
            )

        return await self._persist_preference_rows(session, payload.senha_id, payload.setor_id, payload.respostas)

    async def submit_preference_classification(
        self,
        session: AsyncSession,
        payload: PreferenciaClassificacaoSubmitRequest,
    ) -> FormularioSubmitResponse:
        await self._ensure_senha_belongs_to_setor(session, payload.senha_id, payload.setor_id)
        pergunta_ids = await self._get_question_ids(session, PerguntaPreferencia)
        self._ensure_known_questions(set(payload.mais20), pergunta_ids)
        self._ensure_known_questions(set(payload.mais10), pergunta_ids)
        self._ensure_known_questions(set(payload.menos20), pergunta_ids)
        self._ensure_known_questions(set(payload.menos10), pergunta_ids)

        if not set(payload.mais10).issubset(set(payload.mais20)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="As 10 mais importantes precisam estar dentro das 20 mais importantes",
            )
        if not set(payload.menos10).issubset(set(payload.menos20)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="As 10 menos importantes precisam estar dentro das 20 menos importantes",
            )

        weights = {pergunta_id: 3 for pergunta_id in pergunta_ids}
        for pergunta_id in payload.mais20:
            weights[pergunta_id] = 4
        for pergunta_id in payload.mais10:
            weights[pergunta_id] = 5
        for pergunta_id in payload.menos20:
            weights[pergunta_id] = 2 if weights[pergunta_id] == 3 else 0
        for pergunta_id in payload.menos10:
            weights[pergunta_id] = 1 if weights[pergunta_id] == 2 else 0

        respostas = [
            PreferenciaPesoInput(pergunta_id=pergunta_id, resposta=peso)
            for pergunta_id, peso in weights.items()
        ]
        return await self._persist_preference_rows(session, payload.senha_id, payload.setor_id, respostas)

    async def _persist_preference_rows(
        self,
        session: AsyncSession,
        senha_id: int,
        setor_id: int,
        respostas: list[PreferenciaPesoInput],
    ) -> FormularioSubmitResponse:
        now = datetime.now(timezone.utc)
        rows = [
            {
                "senha_id": senha_id,
                "setor_id": setor_id,
                "pergunta_id": item.pergunta_id,
                "resposta": str(item.resposta),
                "data_resposta": item.data_resposta or now,
            }
            for item in respostas
        ]

        stmt = insert(RespostaPreferencia).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["senha_id", "pergunta_id"],
            set_={
                "setor_id": stmt.excluded.setor_id,
                "resposta": stmt.excluded.resposta,
                "data_resposta": stmt.excluded.data_resposta,
            },
        )
        await session.execute(stmt)

        total_questions = len(await self._get_question_ids(session, PerguntaPreferencia))
        saved_count = await self._count_saved_answers(session, RespostaPreferencia, senha_id)
        if saved_count < total_questions:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formulario de preferencias incompleto",
            )

        await session.execute(
            update(Senha)
            .where(Senha.id == senha_id)
            .values(
                formulario_preferencias_concluido=True,
                formulario_preferencias_concluido_em=now,
            )
        )
        await session.commit()

        return FormularioSubmitResponse(
            senha_id=senha_id,
            formulario="preferencias",
            total_respostas=saved_count,
            concluido=True,
        )

    async def _ensure_senha_belongs_to_setor(
        self,
        session: AsyncSession,
        senha_id: int,
        setor_id: int,
    ) -> None:
        senha = await session.get(Senha, senha_id)
        if senha is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Senha nao encontrada")
        if senha.setor_id != setor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Senha nao pertence ao setor informado",
            )

    async def _get_question_ids(self, session: AsyncSession, model: type) -> set[str]:
        ids = (await session.execute(select(model.id))).scalars().all()
        if not ids:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Formulario sem perguntas cadastradas",
            )
        return set(ids)

    def _ensure_known_questions(self, received_ids: set[str], known_ids: set[str]) -> None:
        unknown = sorted(received_ids - known_ids)
        if unknown:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Perguntas desconhecidas: {', '.join(unknown)}",
            )

    async def _count_saved_answers(
        self,
        session: AsyncSession,
        model: type,
        senha_id: int,
    ) -> int:
        stmt = select(func.count(func.distinct(model.pergunta_id))).where(model.senha_id == senha_id)
        return int((await session.execute(stmt)).scalar_one())
