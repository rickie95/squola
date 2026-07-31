"""init

Revision ID: d796882ee884
Revises: 
Create Date: 2026-02-01 23:26:30.881027

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from squola.models import EnumArray, MatterRequirements


# revision identifiers, used by Alembic.
revision: str = 'd796882ee884'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("schedule_preference", sa.String(length=50), nullable=False),
    )

    op.create_table(
        "teacher_blacklisted_slots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id"), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("hour_slot", sa.Integer(), nullable=False),
    )

    op.create_table(
        "classes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("year", sa.String(length=10), nullable=False),
        sa.Column("section", sa.String(length=5), nullable=False),
    )

    op.create_table(
        "matters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
    )

    op.create_table(
        "teacher_matter",
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id"), primary_key=True),
        sa.Column("matter_id", sa.Integer(), sa.ForeignKey("matters.id"), primary_key=True),
    )

    op.create_table(
        "class_matter_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column("matter_id", sa.Integer(), sa.ForeignKey("matters.id"), nullable=False),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id"), nullable=False),
        sa.Column("hours_per_week", sa.Integer(), nullable=False),
        sa.Column("requirements", EnumArray(MatterRequirements), nullable=True),
        sa.UniqueConstraint("class_id", "matter_id", name="uq_class_matter"),
    )

    op.create_table(
        "saved_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("nickname", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("solve_time_seconds", sa.Float(), nullable=False),
        sa.Column("total_slots", sa.Integer(), nullable=False),
        sa.Column("schedule_data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("saved_schedules")
    op.drop_table("class_matter_assignments")
    op.drop_table("teacher_matter")
    op.drop_table("matters")
    op.drop_table("classes")
    op.drop_table("teacher_blacklisted_slots")
    op.drop_table("teachers")
