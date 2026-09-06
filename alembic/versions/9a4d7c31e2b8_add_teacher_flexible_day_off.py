"""add teacher flexible day off

Revision ID: 9a4d7c31e2b8
Revises: 3f1d4bf7f8de
Create Date: 2026-09-06 15:33:17.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a4d7c31e2b8"
down_revision: Union[str, Sequence[str], None] = "3f1d4bf7f8de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("teachers") as batch_op:
        batch_op.add_column(
            sa.Column(
                "prefers_day_off",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("teachers") as batch_op:
        batch_op.drop_column("prefers_day_off")
