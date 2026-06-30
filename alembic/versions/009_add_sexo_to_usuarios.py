"""add sexo to usuarios

Revision ID: 009
Revises: 008
Create Date: 2026-07-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column("sexo", sa.Text(), nullable=True),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column("usuarios", "sexo", schema="public")
