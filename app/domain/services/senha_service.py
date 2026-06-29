from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import Senha, Setor
from app.schemas.senhas import GenerateSenhasRequest, GenerateSenhasResponse, SenhaRead
from app.utils.passwords import generate_password


class SenhaService:
    async def list_by_setor(self, session: AsyncSession, setor_id: int) -> list[SenhaRead]:
        await self._ensure_setor_exists(session, setor_id)
        stmt = select(Senha).where(Senha.setor_id == setor_id).order_by(Senha.created_at.desc())
        senhas = (await session.execute(stmt)).scalars().all()
        return [self._to_schema(senha) for senha in senhas]

    async def generate(self, session: AsyncSession, payload: GenerateSenhasRequest) -> GenerateSenhasResponse:
        await self._ensure_setor_exists(session, payload.setor_id)

        existing = set((await session.execute(select(Senha.senha))).scalars().all())
        new_passwords: list[str] = []

        while len(new_passwords) < payload.quantidade:
            candidate = generate_password()
            if candidate in existing:
                continue
            existing.add(candidate)
            new_passwords.append(candidate)

        rows = [Senha(senha=password, setor_id=payload.setor_id) for password in new_passwords]
        session.add_all(rows)
        await session.commit()

        for row in rows:
            await session.refresh(row)

        return GenerateSenhasResponse(
            setor_id=payload.setor_id,
            senhas=[self._to_schema(row) for row in rows],
        )

    async def delete(self, session: AsyncSession, senha_id: int) -> None:
        result = await session.execute(delete(Senha).where(Senha.id == senha_id).returning(Senha.id))
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Senha nao encontrada")
        await session.commit()

    async def _ensure_setor_exists(self, session: AsyncSession, setor_id: int) -> None:
        setor = await session.get(Setor, setor_id)
        if setor is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setor nao encontrado")

    def _to_schema(self, senha: Senha) -> SenhaRead:
        return SenhaRead(
            id=senha.id,
            senha=senha.senha,
            setor_id=senha.setor_id,
            formulario_opcoes_concluido=bool(senha.formulario_opcoes_concluido),
            formulario_preferencias_concluido=bool(senha.formulario_preferencias_concluido),
            formulario_opcoes_concluido_em=senha.formulario_opcoes_concluido_em,
            formulario_preferencias_concluido_em=senha.formulario_preferencias_concluido_em,
            created_at=senha.created_at,
        )
