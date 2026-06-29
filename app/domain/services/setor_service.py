from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import Senha, Setor
from app.schemas.setores import SetorCreate, SetorRead, SetorSummary, SetorUpdate


class SetorService:
    async def list_setores(self, session: AsyncSession) -> list[SetorSummary]:
        setores = (await session.execute(select(Setor).order_by(Setor.nome))).scalars().all()
        senhas = (await session.execute(select(Senha))).scalars().all()

        total_counts: dict[int, int] = {}
        complete_counts: dict[int, int] = {}
        for senha in senhas:
            total_counts[senha.setor_id] = total_counts.get(senha.setor_id, 0) + 1
            if senha.formulario_opcoes_concluido and senha.formulario_preferencias_concluido:
                complete_counts[senha.setor_id] = complete_counts.get(senha.setor_id, 0) + 1

        return [
            SetorSummary(
                id=setor.id,
                nome=setor.nome,
                created_at=setor.created_at,
                quantidade_senhas=total_counts.get(setor.id, 0),
                senhas_respondidas=complete_counts.get(setor.id, 0),
            )
            for setor in setores
        ]

    async def create_setor(self, session: AsyncSession, payload: SetorCreate) -> SetorRead:
        nome = payload.nome.strip()
        if not nome:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nome obrigatorio")

        setor = Setor(nome=nome)
        session.add(setor)
        await session.commit()
        await session.refresh(setor)
        return SetorRead(id=setor.id, nome=setor.nome, created_at=setor.created_at)

    async def update_setor(
        self,
        session: AsyncSession,
        setor_id: int,
        payload: SetorUpdate,
    ) -> SetorRead:
        nome = payload.nome.strip()
        if not nome:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nome obrigatorio")

        result = await session.execute(
            update(Setor).where(Setor.id == setor_id).values(nome=nome).returning(Setor)
        )
        setor = result.scalar_one_or_none()
        if setor is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setor nao encontrado")

        await session.commit()
        return SetorRead(id=setor.id, nome=setor.nome, created_at=setor.created_at)

    async def delete_setor(self, session: AsyncSession, setor_id: int) -> None:
        result = await session.execute(delete(Setor).where(Setor.id == setor_id).returning(Setor.id))
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setor nao encontrado")
        await session.commit()
