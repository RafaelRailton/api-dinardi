from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import (
    PerguntaCultura,
    PerguntaOpcao,
    PerguntaPreferencia,
    RespostaCultura,
    RespostaOpcao,
    RespostaPreferencia,
    Senha,
)
from app.schemas.questions import PerguntaCulturaRead, PerguntaOpcaoRead, PerguntaPreferenciaRead
from app.schemas.responses import (
    CulturaPerfilScore,
    CulturaRespostaSalva,
    CulturaResultadoResponse,
    CulturaSubmitRequest,
    CulturaSubmitResponse,
    FormularioSubmitResponse,
    OpcaoSubmitRequest,
    PreferenciaClassificacaoSubmitRequest,
    PreferenciaPesoInput,
    PreferenciaPesosSubmitRequest,
)
from app.utils.sanitize import sanitize_cultura_resposta, sanitize_int, sanitize_str


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
                "resposta": sanitize_int(item.resposta, 0),
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
        all_ids = await self._get_question_ids(session, PerguntaPreferencia)

        all_submitted = set()
        for ids in payload.rounds:
            all_submitted.update(ids)
        self._ensure_known_questions(all_submitted, all_ids)

        weights: dict[str, int] = {pid: 3 for pid in all_ids}

        for pid in payload.rounds[0]:
            if pid in weights:
                weights[pid] = 4

        for pid in payload.rounds[1]:
            if pid in weights:
                weights[pid] = 5

        for pid in payload.rounds[2]:
            if pid in weights:
                weights[pid] = 0 if weights[pid] != 3 else 2

        for pid in payload.rounds[3]:
            if pid in weights:
                weights[pid] = 0 if weights[pid] == 0 else 1

        respostas = [
            PreferenciaPesoInput(pergunta_id=pid, resposta=peso)
            for pid, peso in weights.items()
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
                "resposta": sanitize_str(str(item.resposta), "0"),
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

    async def list_cultura(self, session: AsyncSession) -> list[PerguntaCulturaRead]:
        rows = (
            await session.execute(select(PerguntaCultura).order_by(PerguntaCultura.ordem))
        ).scalars().all()
        return [
            PerguntaCulturaRead(
                id=row.id,
                categoria=row.categoria,
                pergunta=row.pergunta,
                tipo=row.tipo,
                opcoes=row.opcoes,
                ordem=row.ordem,
            )
            for row in rows
        ]

    async def get_cultura_respostas(
        self,
        session: AsyncSession,
        senha_id: int,
    ) -> list[CulturaRespostaSalva]:
        rows = (
            await session.execute(
                select(RespostaCultura).where(RespostaCultura.senha_id == senha_id)
            )
        ).scalars().all()
        return [
            CulturaRespostaSalva(
                pergunta_id=row.pergunta_id,
                resposta=row.resposta,
                data_resposta=row.data_resposta,
            )
            for row in rows
        ]

    async def salvar_resposta_cultura(
        self,
        session: AsyncSession,
        senha_id: int,
        setor_id: int,
        pergunta_id: str,
        resposta: dict,
    ) -> None:
        formatted = sanitize_cultura_resposta(resposta)

        stmt = insert(RespostaCultura).values(
            senha_id=senha_id,
            setor_id=setor_id,
            pergunta_id=pergunta_id,
            resposta=formatted,
            data_resposta=datetime.now(timezone.utc),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["senha_id", "pergunta_id"],
            set_={
                "setor_id": stmt.excluded.setor_id,
                "resposta": stmt.excluded.resposta,
                "data_resposta": stmt.excluded.data_resposta,
            },
        )
        await session.execute(stmt)
        await session.commit()

    async def submit_cultura(
        self,
        session: AsyncSession,
        payload: CulturaSubmitRequest,
    ) -> CulturaSubmitResponse:
        await self._ensure_senha_belongs_to_setor(session, payload.senha_id, payload.setor_id)
        pergunta_ids = await self._get_question_ids(session, PerguntaCultura)
        received_ids = {item.pergunta_id for item in payload.respostas}
        self._ensure_known_questions(received_ids, pergunta_ids)

        if received_ids != pergunta_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formulario de cultura incompleto: todas as 6 perguntas devem ser respondidas",
            )

        now = datetime.now(timezone.utc)
        rows = [
            {
                "senha_id": payload.senha_id,
                "setor_id": payload.setor_id,
                "pergunta_id": item.pergunta_id,
                "resposta": sanitize_cultura_resposta({
                    codigo: {"atual": val.atual}
                    for codigo, val in item.resposta.items()
                }),
                "data_resposta": item.data_resposta or now,
            }
            for item in payload.respostas
        ]

        stmt = insert(RespostaCultura).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["senha_id", "pergunta_id"],
            set_={
                "setor_id": stmt.excluded.setor_id,
                "resposta": stmt.excluded.resposta,
                "data_resposta": stmt.excluded.data_resposta,
            },
        )
        await session.execute(stmt)

        saved_count = await self._count_saved_answers(session, RespostaCultura, payload.senha_id)
        if saved_count < len(pergunta_ids):
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formulario de cultura incompleto",
            )

        await session.execute(
            update(Senha)
            .where(Senha.id == payload.senha_id)
            .values(
                formulario_cultura_concluido=True,
                formulario_cultura_concluido_em=now,
            )
        )
        await session.commit()

        resultado = await self.calculate_cultura_result(session, payload.senha_id)

        return CulturaSubmitResponse(
            senha_id=payload.senha_id,
            formulario="cultura",
            total_respostas=saved_count,
            concluido=True,
            resultado=resultado,
        )

    async def calculate_cultura_result(
        self,
        session: AsyncSession,
        senha_id: int,
    ) -> CulturaResultadoResponse:
        respostas = (
            await session.execute(
                select(RespostaCultura).where(RespostaCultura.senha_id == senha_id)
            )
        ).scalars().all()

        if not respostas:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhuma resposta de cultura encontrada para esta senha",
            )

        perfil_map = {
            "A": "colaborar",
            "B": "criar",
            "C": "competir",
            "D": "controlar",
        }
        perfil_nomes = {
            "colaborar": "Colaborar",
            "criar": "Criar",
            "competir": "Competir",
            "controlar": "Controlar",
        }

        somas = {
            "colaborar": 0,
            "criar": 0,
            "competir": 0,
            "controlar": 0,
        }

        for resposta in respostas:
            for codigo, perfil in perfil_map.items():
                valores = resposta.resposta.get(codigo, {})
                somas[perfil] += valores.get("atual", 0)

        n = len(respostas)
        scores: list[CulturaPerfilScore] = []
        for perfil in ["colaborar", "criar", "competir", "controlar"]:
            atual = round(somas[perfil] / n, 2)
            scores.append(CulturaPerfilScore(
                perfil=perfil,
                nome=perfil_nomes[perfil],
                atual=atual,
            ))

        dominante_atual = max(scores, key=lambda s: s.atual).perfil

        return CulturaResultadoResponse(
            senha_id=senha_id,
            scores=scores,
            perfil_dominante_atual=dominante_atual,
        )

    async def aggregate_cultura_results(
        self,
        session: AsyncSession,
        setor_id: int | None = None,
    ) -> dict:
        stmt = select(RespostaCultura)
        if setor_id is not None:
            stmt = stmt.join(Senha, RespostaCultura.senha_id == Senha.id).where(
                Senha.setor_id == setor_id
            )
        respostas = (await session.execute(stmt)).scalars().all()

        if not respostas:
            return {
                "total_respondentes": 0,
                "scores_medios": [],
                "perfil_dominante_atual": "",
            }

        senha_ids = list(set(r.senha_id for r in respostas))
        n_respondentes = len(senha_ids)

        perfil_map = {
            "A": "colaborar",
            "B": "criar",
            "C": "competir",
            "D": "controlar",
        }
        perfil_nomes = {
            "colaborar": "Colaborar",
            "criar": "Criar",
            "competir": "Competir",
            "controlar": "Controlar",
        }

        totals = {
            "colaborar": 0.0,
            "criar": 0.0,
            "competir": 0.0,
            "controlar": 0.0,
        }

        for resposta in respostas:
            for codigo, perfil in perfil_map.items():
                valores = resposta.resposta.get(codigo, {})
                totals[perfil] += valores.get("atual", 0)

        scores = []
        for perfil in ["colaborar", "criar", "competir", "controlar"]:
            atual = round(totals[perfil] / n_respondentes, 2) if n_respondentes else 0
            scores.append({
                "perfil": perfil,
                "nome": perfil_nomes[perfil],
                "atual": atual,
            })

        dominante_atual = max(scores, key=lambda s: s["atual"])["perfil"] if scores else ""

        return {
            "total_respondentes": n_respondentes,
            "scores_medios": scores,
            "perfil_dominante_atual": dominante_atual,
        }

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
