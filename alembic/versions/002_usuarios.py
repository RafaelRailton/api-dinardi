"""create usuarios table

Revision ID: 002
Revises: 001
Create Date: 2026-06-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.Text(), nullable=False),
        sa.Column("cpf", sa.Text(), nullable=False, unique=True),
        sa.Column("funcao", sa.Text(), nullable=True),
        sa.Column("setor", sa.Text(), nullable=True),
        sa.Column("matricula", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="public",
    )


def downgrade() -> None:
    op.drop_table("usuarios", schema="public")
