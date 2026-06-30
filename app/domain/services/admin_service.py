from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import (
    PerguntaCultura,
    PerguntaOpcao,
    PerguntaPreferencia,
    RespostaCultura,
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
        perguntas_cultura = (
            await session.execute(select(PerguntaCultura).order_by(PerguntaCultura.ordem))
        ).scalars().all()
        respostas_opcoes = (await session.execute(select(RespostaOpcao))).scalars().all()
        respostas_preferencias = (await session.execute(select(RespostaPreferencia))).scalars().all()
        respostas_cultura = (await session.execute(select(RespostaCultura))).scalars().all()

        setores_map = {setor.id: setor.nome for setor in setores}
        respostas_opcoes_map = {
            (resposta.senha_id, resposta.pergunta_id): resposta.resposta
            for resposta in respostas_opcoes
        }
        respostas_preferencias_map = {
            (resposta.senha_id, resposta.pergunta_id): resposta.resposta
            for resposta in respostas_preferencias
        }
        respostas_cultura_map = {
            resposta.senha_id: resposta
            for resposta in respostas_cultura
        }

        def _calc_cultura_scores(senha_id):
            scores = {"colaborar": 0, "criar": 0, "competir": 0, "controlar": 0}
            cultura = [r for r in respostas_cultura if r.senha_id == senha_id]
            perfil_map = {"A": "colaborar", "B": "criar", "C": "competir", "D": "controlar"}
            for r in cultura:
                for codigo, perfil in perfil_map.items():
                    valores = r.resposta.get(codigo, {})
                    scores[perfil] += valores.get("atual", 0)
            n = len(cultura)
            if n > 0:
                for p in scores:
                    scores[p] = round(scores[p] / n, 2)
            return scores

        rows: list[ExportRow] = []
        for senha in senhas:
            respostas: dict[str, str | int | None] = {}
            for pergunta in perguntas_opcoes:
                key = f"op_{pergunta.id} - {pergunta.pergunta}"
                respostas[key] = respostas_opcoes_map.get((senha.id, pergunta.id))
            for pergunta in perguntas_preferencias:
                key = f"pref_{pergunta.id} - {pergunta.pergunta}"
                respostas[key] = respostas_preferencias_map.get((senha.id, pergunta.id))

            cultura_scores = _calc_cultura_scores(senha.id)
            for pergunta in perguntas_cultura:
                cultura = next((r for r in respostas_cultura if r.senha_id == senha.id and r.pergunta_id == pergunta.id), None)
                if cultura:
                    for codigo in ["A", "B", "C", "D"]:
                        val = cultura.resposta.get(codigo, {})
                        respostas[f"cultura_{pergunta.id}_{codigo}_atual"] = val.get("atual")

            for perfil in ["colaborar", "criar", "competir", "controlar"]:
                respostas[f"cultura_media_{perfil}_atual"] = cultura_scores[perfil]

            scores_list = [(p, cultura_scores[p]) for p in ["colaborar", "criar", "competir", "controlar"]]
            respostas["cultura_perfil_dominante_atual"] = max(scores_list, key=lambda x: x[1])[0] if scores_list else None
            respostas["formulario_cultura_concluido"] = bool(senha.formulario_cultura_concluido)
            respostas["formulario_cultura_concluido_em"] = str(senha.formulario_cultura_concluido_em) if senha.formulario_cultura_concluido_em else None

            rows.append(
                ExportRow(
                    setor=setores_map.get(senha.setor_id, ""),
                    senha=senha.senha,
                    respostas=respostas,
                )
            )

        return rows

    async def export_tabs(self, session: AsyncSession) -> dict[str, list[dict]]:
        usuarios = (await session.execute(
            select(Usuario, Senha).join(Senha, Senha.senha == Usuario.cpf)
        )).all()

        user_map: dict[int, dict] = {}
        for usuario, senha in usuarios:
            user_map[senha.id] = {
                "nome": usuario.nome,
                "cpf": usuario.cpf,
                "setor_id": senha.setor_id,
                "funcao": usuario.funcao or "",
                "data_contratacao": str(usuario.data_contratacao) if usuario.data_contratacao else "",
                "unidade": usuario.unidade or "",
                "sexo": usuario.sexo or "",
            }

        setores = (await session.execute(select(Setor))).scalars().all()
        setor_names = {s.id: s.nome for s in setores}

        perguntas_opcoes = (await session.execute(
            select(PerguntaOpcao).order_by(PerguntaOpcao.ordem)
        )).scalars().all()
        perguntas_pref = (await session.execute(
            select(PerguntaPreferencia).order_by(PerguntaPreferencia.ordem)
        )).scalars().all()
        perguntas_cultura = (await session.execute(
            select(PerguntaCultura).order_by(PerguntaCultura.ordem)
        )).scalars().all()

        resp_opcoes = (await session.execute(select(RespostaOpcao))).scalars().all()
        resp_pref = (await session.execute(select(RespostaPreferencia))).scalars().all()
        resp_cultura = (await session.execute(select(RespostaCultura))).scalars().all()

        opcoes_by_user: dict[int, dict[str, int]] = {}
        for r in resp_opcoes:
            opcoes_by_user.setdefault(r.senha_id, {})[r.pergunta_id] = r.resposta

        pref_by_user: dict[int, dict[str, int]] = {}
        for r in resp_pref:
            pref_by_user.setdefault(r.senha_id, {})[r.pergunta_id] = int(r.resposta)

        cultura_by_user: dict[int, dict[str, dict]] = {}
        for r in resp_cultura:
            cultura_by_user.setdefault(r.senha_id, {})[r.pergunta_id] = r.resposta

        opcoes_rows = []
        for senha_id, resp_map in opcoes_by_user.items():
            user = user_map.get(senha_id, {})
            row = {k: v for k, v in user.items() if k != "setor_id"}
            row["setor"] = setor_names.get(user.get("setor_id"), "")
            for p in perguntas_opcoes:
                row[p.id] = resp_map.get(p.id)
            opcoes_rows.append(row)

        pref_rows = []
        for senha_id, resp_map in pref_by_user.items():
            user = user_map.get(senha_id, {})
            row = {k: v for k, v in user.items() if k != "setor_id"}
            row["setor"] = setor_names.get(user.get("setor_id"), "")
            for p in perguntas_pref:
                row[p.id] = resp_map.get(p.id)
            pref_rows.append(row)

        cultura_rows = []
        for senha_id, resp_map in cultura_by_user.items():
            user = user_map.get(senha_id, {})
            row = {k: v for k, v in user.items() if k != "setor_id"}
            row["setor"] = setor_names.get(user.get("setor_id"), "")
            for p in perguntas_cultura:
                vals = resp_map.get(p.id, {})
                for cod in ("A", "B", "C", "D"):
                    row[f"{p.id}_{cod}"] = vals.get(cod, {}).get("atual", 0) if isinstance(vals.get(cod), dict) else 0
            cultura_rows.append(row)

        perguntas_opcoes_dict = {p.id: p for p in perguntas_opcoes}
        perguntas_pref_dict = {p.id: p for p in perguntas_pref}
        perguntas_cultura_dict = {p.id: p for p in perguntas_cultura}

        flat_opcoes = []
        for r in resp_opcoes:
            user = user_map.get(r.senha_id)
            if not user:
                continue
            p = perguntas_opcoes_dict.get(r.pergunta_id)
            opcao_texto = next((o["texto"] for o in p.opcoes if o.get("valor") == r.resposta), "") if p else ""
            flat_opcoes.append({
                **{k: v for k, v in user.items() if k != "setor_id"},
                "setor": setor_names.get(user.get("setor_id"), ""),
                "pergunta_id": r.pergunta_id,
                "pergunta": p.pergunta if p else "",
                "resposta": r.resposta,
                "texto_resposta": opcao_texto,
                "data_resposta": str(r.data_resposta) if r.data_resposta else "",
            })

        flat_pref = []
        for r in resp_pref:
            user = user_map.get(r.senha_id)
            if not user:
                continue
            p = perguntas_pref_dict.get(r.pergunta_id)
            flat_pref.append({
                **{k: v for k, v in user.items() if k != "setor_id"},
                "setor": setor_names.get(user.get("setor_id"), ""),
                "pergunta_id": r.pergunta_id,
                "pergunta": p.pergunta if p else "",
                "peso": int(r.resposta),
                "data_resposta": str(r.data_resposta) if r.data_resposta else "",
            })

        flat_cultura = []
        for r in resp_cultura:
            user = user_map.get(r.senha_id)
            if not user:
                continue
            p = perguntas_cultura_dict.get(r.pergunta_id)
            flat_cultura.append({
                **{k: v for k, v in user.items() if k != "setor_id"},
                "setor": setor_names.get(user.get("setor_id"), ""),
                "pergunta_id": r.pergunta_id,
                "pergunta": p.pergunta if p else "",
                "A": r.resposta.get("A", {}).get("atual", 0) if isinstance(r.resposta.get("A"), dict) else 0,
                "B": r.resposta.get("B", {}).get("atual", 0) if isinstance(r.resposta.get("B"), dict) else 0,
                "C": r.resposta.get("C", {}).get("atual", 0) if isinstance(r.resposta.get("C"), dict) else 0,
                "D": r.resposta.get("D", {}).get("atual", 0) if isinstance(r.resposta.get("D"), dict) else 0,
                "data_resposta": str(r.data_resposta) if r.data_resposta else "",
            })

        return {
            "opcoes": opcoes_rows,
            "preferencias": pref_rows,
            "cultura": cultura_rows,
            "flat": {
                "opcoes": flat_opcoes,
                "preferencias": flat_pref,
                "cultura": flat_cultura,
            },
        }

    async def dashboard(self, session: AsyncSession) -> DashboardResponse:
        total_usuarios = (await session.execute(select(func.count(Usuario.id)))).scalar_one()

        total_resp_opcoes = (
            await session.execute(select(func.count(func.distinct(RespostaOpcao.senha_id))))
        ).scalar_one()

        total_resp_preferencias = (
            await session.execute(select(func.count(func.distinct(RespostaPreferencia.senha_id))))
        ).scalar_one()

        total_resp_cultura = (
            await session.execute(select(func.count(func.distinct(RespostaCultura.senha_id))))
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

            resp_cultura = (
                await session.execute(
                    select(func.count(func.distinct(RespostaCultura.senha_id)))
                    .join(Senha, RespostaCultura.senha_id == Senha.id)
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
                    respostas_cultura=resp_cultura,
                    pendentes_opcoes=total - resp_opcoes,
                    pendentes_preferencias=total - resp_preferencias,
                    pendentes_cultura=total - resp_cultura,
                )
            )

        return DashboardResponse(
            setores=setor_data,
            total_usuarios=total_usuarios,
            total_respostas_opcoes=total_resp_opcoes,
            total_respostas_preferencias=total_resp_preferencias,
            total_respostas_cultura=total_resp_cultura,
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
                "formulario_cultura_concluido": bool(senha.formulario_cultura_concluido) if senha else False,
                "formulario_cultura_concluido_em": str(senha.formulario_cultura_concluido_em) if senha and senha.formulario_cultura_concluido_em else None,
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
            data_contratacao=date.fromisoformat(payload.data_contratacao) if payload.data_contratacao else None,
            unidade=payload.unidade or None,
        )
        session.add(usuario)
        await session.commit()
        await session.refresh(usuario)
        return usuario

    async def preferencias_por_setor(self, session: AsyncSession, setor_id: int | None = None, page: int = 1, page_size: int = 10) -> dict:
        from app.models.tables import PerguntaPreferencia as PP, RespostaPreferencia as RP

        perguntas = (await session.execute(select(PP).order_by(PP.ordem))).scalars().all()
        pergunta_map = {p.id: p.pergunta for p in perguntas}

        stmt = (
            select(Usuario, Senha)
            .join(Senha, Senha.senha == Usuario.cpf)
            .where(Senha.formulario_preferencias_concluido == True)
        )
        if setor_id is not None:
            stmt = stmt.where(Senha.setor_id == setor_id)
        stmt = stmt.order_by(Senha.formulario_preferencias_concluido_em.desc().nulls_last())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        usuarios = (await session.execute(stmt)).all()

        all_senha_ids = [s.id for _, s in usuarios]
        respostas_raw = (
            await session.execute(select(RP).where(RP.senha_id.in_(all_senha_ids)))
        ).scalars().all()
        respostas_map: dict[int, dict[str, int]] = {}
        for r in respostas_raw:
            respostas_map.setdefault(r.senha_id, {})[r.pergunta_id] = int(r.resposta)

        setores_map = {}
        if not setor_id:
            setor_set = {s.setor_id for _, s in usuarios}
            setores = (await session.execute(select(Setor).where(Setor.id.in_(setor_set)))).scalars().all()
            setores_map = {s.id: s.nome for s in setores}

        result = []
        for usuario, senha in usuarios:
            rm = respostas_map.get(senha.id, {})
            preferencias = [
                {"pergunta_id": p.id, "pergunta": p.pergunta, "peso": rm.get(p.id, 3)}
                for p in perguntas
            ]
            result.append({
                "nome": usuario.nome,
                "cpf": usuario.cpf,
                "senha": senha.senha,
                "setor": setores_map.get(senha.setor_id, "") if not setor_id else "",
                "setor_id": senha.setor_id,
                "formulario_preferencias_concluido_em": str(senha.formulario_preferencias_concluido_em) if senha.formulario_preferencias_concluido_em else None,
                "preferencias": preferencias,
            })

        return {"data": result, "total": total, "page": page, "page_size": page_size}

    async def cultura_aggregate(self, session: AsyncSession, setor_id: int | None = None) -> dict:
        from app.models.tables import RespostaCultura as RC, Senha as S
        stmt = select(RC)
        if setor_id is not None:
            stmt = stmt.join(S, RC.senha_id == S.id).where(S.setor_id == setor_id)
        respostas = (await session.execute(stmt)).scalars().all()

        if not respostas:
            return {
                "total_respondentes": 0,
                "scores_medios": [],
                "perfil_dominante_atual": "",
            }

        senha_ids = list(set(r.senha_id for r in respostas))
        n_respondentes = len(senha_ids)

        perfil_map = {"A": "colaborar", "B": "criar", "C": "competir", "D": "controlar"}
        perfil_nomes = {"colaborar": "Colaborar", "criar": "Criar", "competir": "Competir", "controlar": "Controlar"}

        totals = {p: 0.0 for p in perfil_nomes}

        for r in respostas:
            for codigo, perfil in perfil_map.items():
                val = r.resposta.get(codigo, {})
                totals[perfil] += val.get("atual", 0)

        scores = []
        for perfil in ["colaborar", "criar", "competir", "controlar"]:
            atual = round(totals[perfil] / n_respondentes, 2) if n_respondentes else 0
            scores.append({"perfil": perfil, "nome": perfil_nomes[perfil], "atual": atual})

        dom_atual = max(scores, key=lambda s: s["atual"])["perfil"] if scores else ""

        return {
            "total_respondentes": n_respondentes,
            "scores_medios": scores,
            "perfil_dominante_atual": dom_atual,
        }

    async def respondentes_detalhado(
        self,
        session: AsyncSession,
        setor_id: int | None = None,
        page: int = 1,
        page_size: int = 10,
        busca: str | None = None,
    ) -> dict:
        perguntas_opcoes = {p.id: p for p in
            (await session.execute(select(PerguntaOpcao).order_by(PerguntaOpcao.ordem))).scalars().all()}
        perguntas_cultura = {p.id: p for p in
            (await session.execute(select(PerguntaCultura).order_by(PerguntaCultura.ordem))).scalars().all()}
        perguntas_pref = {p.id: p for p in
            (await session.execute(select(PerguntaPreferencia).order_by(PerguntaPreferencia.ordem))).scalars().all()}

        answered = set()
        answered.update((await session.execute(
            select(func.distinct(RespostaOpcao.senha_id))
        )).scalars().all())
        answered.update((await session.execute(
            select(func.distinct(RespostaPreferencia.senha_id))
        )).scalars().all())
        answered.update((await session.execute(
            select(func.distinct(RespostaCultura.senha_id))
        )).scalars().all())

        if not answered:
            return {"data": [], "total": 0, "page": page, "page_size": page_size}

        stmt = select(Usuario, Senha).join(Senha, Senha.senha == Usuario.cpf).where(
            Senha.id.in_(answered)
        )

        if setor_id is not None:
            stmt = stmt.where(Senha.setor_id == setor_id)
        if busca:
            stmt = stmt.where(
                Usuario.nome.ilike(f"%{busca}%") | Usuario.cpf.ilike(f"%{busca}%")
            )

        stmt = stmt.order_by(
            Senha.formulario_cultura_concluido_em.desc().nulls_last(),
            Senha.formulario_preferencias_concluido_em.desc().nulls_last(),
            Usuario.nome,
        )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        rows = (await session.execute(stmt)).all()

        senha_ids = [s.id for _, s in rows]

        resp_opcoes = (await session.execute(
            select(RespostaOpcao).where(RespostaOpcao.senha_id.in_(senha_ids))
        )).scalars().all()
        opcoes_map: dict[int, dict[str, int]] = {}
        for r in resp_opcoes:
            opcoes_map.setdefault(r.senha_id, {})[r.pergunta_id] = r.resposta

        resp_pref = (await session.execute(
            select(RespostaPreferencia).where(RespostaPreferencia.senha_id.in_(senha_ids))
        )).scalars().all()
        pref_map: dict[int, dict[str, int]] = {}
        for r in resp_pref:
            pref_map.setdefault(r.senha_id, {})[r.pergunta_id] = int(r.resposta)

        if perguntas_cultura:
            resp_cultura = (await session.execute(
                select(RespostaCultura).where(RespostaCultura.senha_id.in_(senha_ids))
            )).scalars().all()
            cultura_map: dict[int, dict[str, dict]] = {}
            for r in resp_cultura:
                cultura_map.setdefault(r.senha_id, {})[r.pergunta_id] = r.resposta
        else:
            cultura_map = {}

        setor_names: dict[int, str] = {}
        if setor_id is None:
            setor_ids = {s.setor_id for _, s in rows}
            setores = (await session.execute(select(Setor).where(Setor.id.in_(setor_ids)))).scalars().all()
            setor_names = {s.id: s.nome for s in setores}

        result = []
        for usuario, senha in rows:
            entry: dict = {
                "nome": usuario.nome,
                "cpf": usuario.cpf,
                "senha": senha.senha,
                "setor": setor_names.get(senha.setor_id, "") if setor_id is None else "",
                "setor_id": senha.setor_id,
                "funcao": usuario.funcao or "",
                "data_contratacao": str(usuario.data_contratacao) if usuario.data_contratacao else None,
                "unidade": usuario.unidade or "",
                "sexo": usuario.sexo or "",
                "formulario_opcoes_concluido": bool(senha.formulario_opcoes_concluido),
                "formulario_opcoes_concluido_em": str(senha.formulario_opcoes_concluido_em) if senha.formulario_opcoes_concluido_em else None,
                "formulario_preferencias_concluido": bool(senha.formulario_preferencias_concluido),
                "formulario_preferencias_concluido_em": str(senha.formulario_preferencias_concluido_em) if senha.formulario_preferencias_concluido_em else None,
                "formulario_cultura_concluido": bool(senha.formulario_cultura_concluido),
                "formulario_cultura_concluido_em": str(senha.formulario_cultura_concluido_em) if senha.formulario_cultura_concluido_em else None,
            }

            if perguntas_opcoes:
                om = opcoes_map.get(senha.id, {})
                entry["opcoes"] = [
                    {
                        "pergunta_id": pid,
                        "pergunta": p.pergunta,
                        "resposta": om.get(pid),
                        "texto_resposta": next((o["texto"] for o in p.opcoes if o.get("valor") == om.get(pid)), None) if om.get(pid) is not None else None,
                    }
                    for pid, p in perguntas_opcoes.items()
                ]
            else:
                entry["opcoes"] = []

            if perguntas_pref:
                pm = pref_map.get(senha.id, {})
                entry["preferencias"] = [
                    {
                        "pergunta_id": pid,
                        "pergunta": p.pergunta,
                        "peso": pm.get(pid),
                    }
                    for pid, p in perguntas_pref.items()
                ]
            else:
                entry["preferencias"] = []

            if perguntas_cultura:
                cm = cultura_map.get(senha.id, {})
                entry["cultura"] = [
                    {
                        "pergunta_id": pid,
                        "pergunta": p.pergunta,
                        "resposta": {
                            cod: {"atual": val.get("atual", 0), "futuro": val.get("futuro", 0)}
                            for cod, val in cm.get(pid, {}).items()
                        }                         if pid in cm else {"A": {"atual": 0}, "B": {"atual": 0}, "C": {"atual": 0}, "D": {"atual": 0}},
                    }
                    for pid, p in perguntas_cultura.items()
                ]
            else:
                entry["cultura"] = []

            result.append(entry)

        return {"data": result, "total": total, "page": page, "page_size": page_size}
