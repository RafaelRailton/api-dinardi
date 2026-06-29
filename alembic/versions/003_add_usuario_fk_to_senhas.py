"""add usuario_id fk to senhas

Revision ID: 003
Revises: 002
Create Date: 2026-06-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "senhas",
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        schema="public",
    )
    op.create_foreign_key(
        "fk_senhas_usuario_id",
        "senhas",
        "usuarios",
        ["usuario_id"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_senhas_usuario_id", "senhas", schema="public")
    op.drop_column("senhas", "usuario_id", schema="public")
