from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.tables import Senha, Setor, Usuario
from app.schemas.auth import AdminLoginRequest, AdminSession, RespondentLoginRequest, RespondentSession
from app.utils.cpf import normalize_cpf


class AuthService:
    async def login_respondent(self, session: AsyncSession, payload: RespondentLoginRequest) -> RespondentSession:
        raw = normalize_cpf(payload.cpf).zfill(11)

        usuario = await session.execute(
            select(Usuario).where(Usuario.cpf == raw).options(selectinload(Usuario.setor_rel))
        )
        usuario = usuario.scalar_one_or_none()
        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CPF nao cadastrado. Apenas funcionarios cadastrados podem acessar a pesquisa.",
            )

        setor = usuario.setor_rel

        stmt = select(Senha).where(Senha.senha == raw)
        result = await session.execute(stmt)
        senha_row = result.scalar_one_or_none()

        if senha_row is None:
            senha_row = Senha(senha=raw, setor_id=setor.id, usuario_id=usuario.id)
            session.add(senha_row)
            await session.commit()
            await session.refresh(senha_row)

        return RespondentSession(
            senha_id=senha_row.id,
            senha_codigo=senha_row.senha,
            setor_id=setor.id,
            setor_nome=setor.nome,
            formulario_opcoes_concluido=bool(senha_row.formulario_opcoes_concluido),
            formulario_preferencias_concluido=bool(senha_row.formulario_preferencias_concluido),
            formulario_cultura_concluido=bool(senha_row.formulario_cultura_concluido),
        )

    async def get_respondent_status(self, session: AsyncSession, senha_id: int) -> RespondentSession:
        stmt = (
            select(Senha, Setor)
            .join(Setor, Senha.setor_id == Setor.id)
            .where(Senha.id == senha_id)
        )
        result = await session.execute(stmt)
        row = result.one_or_none()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro nao encontrado",
            )

        senha_row, setor = row
        return RespondentSession(
            senha_id=senha_row.id,
            senha_codigo=senha_row.senha,
            setor_id=senha_row.setor_id,
            setor_nome=setor.nome,
            formulario_opcoes_concluido=bool(senha_row.formulario_opcoes_concluido),
            formulario_preferencias_concluido=bool(senha_row.formulario_preferencias_concluido),
            formulario_cultura_concluido=bool(senha_row.formulario_cultura_concluido),
        )

    async def login_admin(self, payload: AdminLoginRequest) -> AdminSession:
        if payload.email != settings.admin_email or payload.password != settings.admin_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais invalidas",
            )
        return AdminSession(email=payload.email)
