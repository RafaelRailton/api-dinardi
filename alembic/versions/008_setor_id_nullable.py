"""make setor_id nullable on usuarios

Revision ID: 008
Revises: 007
Create Date: 2026-07-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "usuarios",
        "setor_id",
        existing_type=sa.Integer(),
        nullable=True,
        schema="public",
    )


def downgrade() -> None:
    op.alter_column(
        "usuarios",
        "setor_id",
        existing_type=sa.Integer(),
        nullable=False,
        schema="public",
    )
