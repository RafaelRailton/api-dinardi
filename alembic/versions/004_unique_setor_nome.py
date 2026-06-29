"""add unique constraint on setores.nome

Revision ID: 004
Revises: 003
Create Date: 2026-06-26
"""

from typing import Sequence, Union

from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("uq_setores_nome", "setores", ["nome"], schema="public")


def downgrade() -> None:
    op.drop_constraint("uq_setores_nome", "setores", schema="public")
