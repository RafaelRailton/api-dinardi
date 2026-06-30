"""add data_contratacao e unidade to usuarios

Revision ID: 007
Revises: 006
Create Date: 2026-07-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column("data_contratacao", sa.Date(), nullable=True),
        schema="public",
    )
    op.add_column(
        "usuarios",
        sa.Column("unidade", sa.Text(), nullable=True),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column("usuarios", "unidade", schema="public")
    op.drop_column("usuarios", "data_contratacao", schema="public")
