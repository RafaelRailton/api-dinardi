from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import (
    PerguntaOpcao,
    PerguntaPreferencia,
    RespostaOpcao,
    RespostaPreferencia,
    Senha,
    Setor,
    Usuario,
)
from app.schemas.admin import (
    CriarUsuarioRequest,
    DashboardResponse,
    ExportRow,
    SetorDashboard,
)
from app.utils.cpf import normalize_cpf


class AdminService:
    async def export_rows(self, session: AsyncSession) -> list[ExportRow]:
        setores = (await session.execute(select(Setor))).scalars().all()
        senhas = (await session.execute(select(Senha).order_by(Senha.id))).scalars().all()
        perguntas_opcoes = (
            await session.execute(select(PerguntaOpcao).order_by(PerguntaOpcao.ordem))
        ).scalars().all()
        perguntas_preferencias = (
            await session.execute(select(PerguntaPreferencia).order_by(PerguntaPreferencia.ordem))
        ).scalars().all()
        respostas_opcoes = (await session.execute(select(RespostaOpcao))).scalars().all()
        respostas_preferencias = (await session.execute(select(RespostaPreferencia))).scalars().all()

        setores_map = {setor.id: setor.nome for setor in setores}
        respostas_opcoes_map = {
            (resposta.senha_id, resposta.pergunta_id): resposta.resposta
            for resposta in respostas_opcoes
        }
        respostas_preferencias_map = {
            (resposta.senha_id, resposta.pergunta_id): resposta.resposta
            for resposta in respostas_preferencias
        }

        rows: list[ExportRow] = []
        for senha in senhas:
            respostas: dict[str, str | int | None] = {}
            for pergunta in perguntas_opcoes:
                key = f"{pergunta.id} - {pergunta.pergunta}"
                respostas[key] = respostas_opcoes_map.get((senha.id, pergunta.id))
            for pergunta in perguntas_preferencias:
                key = f"{pergunta.id} - {pergunta.pergunta}"
                respostas[key] = respostas_preferencias_map.get((senha.id, pergunta.id))

            rows.append(
                ExportRow(
                    setor=setores_map.get(senha.setor_id, ""),
                    senha=senha.senha,
                    respostas=respostas,
                )
            )

        return rows

    async def dashboard(self, session: AsyncSession) -> DashboardResponse:
        total_usuarios = (await session.execute(select(func.count(Usuario.id)))).scalar_one()

        total_resp_opcoes = (
            await session.execute(select(func.count(func.distinct(RespostaOpcao.senha_id))))
        ).scalar_one()

        total_resp_preferencias = (
            await session.execute(select(func.count(func.distinct(RespostaPreferencia.senha_id))))
        ).scalar_one()

        setores = (await session.execute(select(Setor).order_by(Setor.nome))).scalars().all()
        setor_data: list[SetorDashboard] = []

        for setor in setores:
            total = (
                await session.execute(
                    select(func.count(Usuario.id)).where(Usuario.setor_id == setor.id)
                )
            ).scalar_one()

            resp_opcoes = (
                await session.execute(
                    select(func.count(func.distinct(RespostaOpcao.senha_id)))
                    .join(Senha, RespostaOpcao.senha_id == Senha.id)
                    .where(Senha.setor_id == setor.id)
                )
            ).scalar_one()

            resp_preferencias = (
                await session.execute(
                    select(func.count(func.distinct(RespostaPreferencia.senha_id)))
                    .join(Senha, RespostaPreferencia.senha_id == Senha.id)
                    .where(Senha.setor_id == setor.id)
                )
            ).scalar_one()

            setor_data.append(
                SetorDashboard(
                    setor_id=setor.id,
                    setor_nome=setor.nome,
                    total_usuarios=total,
                    respostas_opcoes=resp_opcoes,
                    respostas_preferencias=resp_preferencias,
                    pendentes_opcoes=total - resp_opcoes,
                    pendentes_preferencias=total - resp_preferencias,
                )
            )

        return DashboardResponse(
            setores=setor_data,
            total_usuarios=total_usuarios,
            total_respostas_opcoes=total_resp_opcoes,
            total_respostas_preferencias=total_resp_preferencias,
        )

    async def respondentes_por_setor(self, session: AsyncSession, setor_id: int) -> list[dict]:
        from app.schemas.admin import RespondenteLog
        stmt = (
            select(Usuario, Senha)
            .join(Senha, Senha.senha == Usuario.cpf, isouter=True)
            .where(Usuario.setor_id == setor_id)
            .order_by(Usuario.nome)
        )
        rows = (await session.execute(stmt)).all()
        result = []
        for usuario, senha in rows:
            result.append({
                "nome": usuario.nome,
                "cpf": usuario.cpf,
                "formulario_opcoes_concluido": bool(senha.formulario_opcoes_concluido) if senha else False,
                "formulario_opcoes_concluido_em": str(senha.formulario_opcoes_concluido_em) if senha and senha.formulario_opcoes_concluido_em else None,
                "formulario_preferencias_concluido": bool(senha.formulario_preferencias_concluido) if senha else False,
                "formulario_preferencias_concluido_em": str(senha.formulario_preferencias_concluido_em) if senha and senha.formulario_preferencias_concluido_em else None,
            })
        return result

    async def criar_usuario(self, session: AsyncSession, payload: CriarUsuarioRequest) -> Usuario:
        raw = normalize_cpf(payload.cpf).zfill(11)

        setor = await session.get(Setor, payload.setor_id)
        if setor is None:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setor nao encontrado")

        from sqlalchemy import select
        existing = (await session.execute(select(Usuario).where(Usuario.cpf == raw))).scalar_one_or_none()
        if existing is not None:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF ja cadastrado")

        usuario = Usuario(
            nome=payload.nome,
            cpf=raw,
            setor_id=payload.setor_id,
            funcao=payload.funcao,
            matricula=payload.matricula,
        )
        session.add(usuario)
        await session.commit()
        await session.refresh(usuario)
        return usuario
