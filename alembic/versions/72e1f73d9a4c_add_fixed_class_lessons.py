"""add fixed class lessons

Revision ID: 72e1f73d9a4c
Revises: 9a4d7c31e2b8
Create Date: 2026-09-09 13:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "72e1f73d9a4c"
down_revision: Union[str, Sequence[str], None] = "9a4d7c31e2b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not sa.inspect(op.get_bind()).has_table("fixed_class_lessons"):
        op.create_table(
            "fixed_class_lessons",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "workspace_id",
                sa.Integer(),
                sa.ForeignKey("workspaces.id"),
                nullable=False,
            ),
            sa.Column(
                "class_id",
                sa.Integer(),
                sa.ForeignKey("classes.id"),
                nullable=False,
            ),
            sa.Column(
                "assignment_id",
                sa.Integer(),
                sa.ForeignKey("class_matter_assignments.id"),
                nullable=False,
            ),
            sa.Column("day_of_week", sa.Integer(), nullable=False),
            sa.Column("hour_slot", sa.Integer(), nullable=False),
            sa.UniqueConstraint(
                "class_id",
                "day_of_week",
                "hour_slot",
                name="uq_fixed_class_lesson_slot",
            ),
        )
        op.create_index(
            "ix_fixed_class_lessons_workspace_id",
            "fixed_class_lessons",
            ["workspace_id"],
        )


def downgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("fixed_class_lessons"):
        op.drop_index(
            "ix_fixed_class_lessons_workspace_id",
            table_name="fixed_class_lessons",
        )
        op.drop_table("fixed_class_lessons")
