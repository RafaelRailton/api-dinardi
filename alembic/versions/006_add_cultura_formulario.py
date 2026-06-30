"""add cultura formulario

Revision ID: 006
Revises: 005
Create Date: 2026-07-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "senhas",
        sa.Column("formulario_cultura_concluido", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        schema="public",
    )
    op.add_column(
        "senhas",
        sa.Column("formulario_cultura_concluido_em", sa.DateTime(timezone=True), nullable=True),
        schema="public",
    )

    op.create_table(
        "perguntas_cultura",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("categoria", sa.Text(), nullable=False),
        sa.Column("pergunta", sa.Text(), nullable=False),
        sa.Column("tipo", sa.Text(), nullable=False),
        sa.Column("opcoes", postgresql.JSONB(), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )

    op.create_table(
        "respostas_cultura",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("senha_id", sa.Integer(), nullable=False),
        sa.Column("setor_id", sa.Integer(), nullable=False),
        sa.Column("pergunta_id", sa.Text(), nullable=False),
        sa.Column("resposta", postgresql.JSONB(), nullable=False),
        sa.Column("data_resposta", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["senha_id"], ["public.senhas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["setor_id"], ["public.setores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pergunta_id"], ["public.perguntas_cultura.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("senha_id", "pergunta_id", name="respostas_cultura_unique_resposta"),
        schema="public",
    )


def downgrade() -> None:
    op.drop_table("respostas_cultura", schema="public")
    op.drop_table("perguntas_cultura", schema="public")
    op.drop_column("senhas", "formulario_cultura_concluido_em", schema="public")
    op.drop_column("senhas", "formulario_cultura_concluido", schema="public")
