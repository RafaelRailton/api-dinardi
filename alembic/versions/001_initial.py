"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "setores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="public",
    )

    op.create_table(
        "senhas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("senha", sa.Text(), nullable=False, unique=True),
        sa.Column(
            "setor_id",
            sa.Integer(),
            sa.ForeignKey("public.setores.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("formulario_opcoes_concluido", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("formulario_preferencias_concluido", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("formulario_opcoes_concluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("formulario_preferencias_concluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="public",
    )

    op.create_table(
        "perguntas_opcoes",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("categoria", sa.Text(), nullable=False),
        sa.Column("pergunta", sa.Text(), nullable=False),
        sa.Column("tipo", sa.Text(), nullable=False),
        sa.Column("opcoes", JSONB(), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        schema="public",
    )

    op.create_table(
        "respostas_opcoes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "senha_id",
            sa.Integer(),
            sa.ForeignKey("public.senhas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "setor_id",
            sa.Integer(),
            sa.ForeignKey("public.setores.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pergunta_id",
            sa.Text(),
            sa.ForeignKey("public.perguntas_opcoes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("resposta", sa.Integer(), nullable=False),
        sa.Column("data_resposta", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("senha_id", "pergunta_id", name="respostas_opcoes_unique_resposta"),
        schema="public",
    )
    op.create_index("idx_respostas_opcoes_senha_id", "respostas_opcoes", ["senha_id"], schema="public")
    op.create_index("idx_respostas_opcoes_setor_id", "respostas_opcoes", ["setor_id"], schema="public")
    op.create_index("idx_respostas_opcoes_pergunta_id", "respostas_opcoes", ["pergunta_id"], schema="public")

    op.create_table(
        "perguntas_preferencias",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("categoria", sa.Text(), nullable=False),
        sa.Column("pergunta", sa.Text(), nullable=False),
        sa.Column("tipo", sa.Text(), nullable=False),
        sa.Column("opcoes", JSONB(), nullable=False),
        sa.Column("peso", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("ordem", sa.Integer(), nullable=False),
        schema="public",
    )

    op.create_table(
        "respostas_preferencias",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "senha_id",
            sa.Integer(),
            sa.ForeignKey("public.senhas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "setor_id",
            sa.Integer(),
            sa.ForeignKey("public.setores.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pergunta_id",
            sa.Text(),
            sa.ForeignKey("public.perguntas_preferencias.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("resposta", sa.Text(), nullable=False),
        sa.Column("data_resposta", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("senha_id", "pergunta_id", name="respostas_preferencias_unique_resposta"),
        schema="public",
    )
    op.create_index("idx_respostas_preferencias_senha_id", "respostas_preferencias", ["senha_id"], schema="public")
    op.create_index("idx_respostas_preferencias_setor_id", "respostas_preferencias", ["setor_id"], schema="public")
    op.create_index("idx_respostas_preferencias_pergunta_id", "respostas_preferencias", ["pergunta_id"], schema="public")

    op.create_table(
        "progresso_respondente",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "senha_id",
            sa.Integer(),
            sa.ForeignKey("public.senhas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("formulario", sa.Text(), nullable=False),
        sa.Column("respostas", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("pergunta_atual", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("concluido", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("senha_id", "formulario"),
        schema="public",
    )
    op.create_index("idx_progresso_respondente_senha_id", "progresso_respondente", ["senha_id"], schema="public")


def downgrade() -> None:
    op.drop_table("progresso_respondente", schema="public")
    op.drop_table("respostas_preferencias", schema="public")
    op.drop_table("perguntas_preferencias", schema="public")
    op.drop_table("respostas_opcoes", schema="public")
    op.drop_table("perguntas_opcoes", schema="public")
    op.drop_table("senhas", schema="public")
    op.drop_table("setores", schema="public")
