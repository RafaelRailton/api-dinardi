"""add setor_id fk to usuarios

Revision ID: 005
Revises: 004
Create Date: 2026-06-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column("setor_id", sa.Integer(), nullable=True),
        schema="public",
    )
    op.execute("""
        UPDATE public.usuarios u
        SET setor_id = s.id
        FROM public.setores s
        WHERE u.setor = s.nome
    """)
    op.alter_column("usuarios", "setor_id", nullable=False, schema="public")
    op.create_foreign_key(
        "fk_usuarios_setor_id",
        "usuarios",
        "setores",
        ["setor_id"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_usuarios_setor_id", "usuarios", schema="public")
    op.drop_column("usuarios", "setor_id", schema="public")
