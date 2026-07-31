"""workspace multiuser foundation

Revision ID: 3f1d4bf7f8de
Revises: 8ccd0fa8406d
Create Date: 2026-07-31 14:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3f1d4bf7f8de"
down_revision: Union[str, Sequence[str], None] = "8ccd0fa8406d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=100), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "workspaces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "workspace_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_membership"),
    )

    op.create_table(
        "auth_sessions",
        sa.Column("token_hash", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )

    with op.batch_alter_table("teachers") as batch_op:
        batch_op.add_column(sa.Column("workspace_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_teachers_workspace_id", ["workspace_id"])
        batch_op.create_foreign_key("fk_teachers_workspace", "workspaces", ["workspace_id"], ["id"])

    with op.batch_alter_table("teacher_unavailabilities") as batch_op:
        batch_op.add_column(sa.Column("workspace_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_teacher_unavailabilities_workspace_id", ["workspace_id"])
        batch_op.create_foreign_key(
            "fk_teacher_unavailabilities_workspace",
            "workspaces",
            ["workspace_id"],
            ["id"],
        )
        batch_op.create_unique_constraint(
            "uq_teacher_unavailability_slot", ["teacher_id", "day_of_week", "hour_slot"]
        )

    with op.batch_alter_table("classes") as batch_op:
        batch_op.add_column(sa.Column("workspace_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_classes_workspace_id", ["workspace_id"])
        batch_op.create_foreign_key("fk_classes_workspace", "workspaces", ["workspace_id"], ["id"])
        batch_op.create_unique_constraint("uq_workspace_class", ["workspace_id", "year", "section"])

    with op.batch_alter_table("matters") as batch_op:
        batch_op.add_column(sa.Column("workspace_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_matters_workspace_id", ["workspace_id"])
        batch_op.create_foreign_key("fk_matters_workspace", "workspaces", ["workspace_id"], ["id"])
        batch_op.create_unique_constraint("uq_workspace_matter_name", ["workspace_id", "name"])

    with op.batch_alter_table("class_matter_assignments") as batch_op:
        batch_op.add_column(sa.Column("workspace_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_class_matter_assignments_workspace_id", ["workspace_id"])
        batch_op.create_foreign_key(
            "fk_class_matter_assignments_workspace",
            "workspaces",
            ["workspace_id"],
            ["id"],
        )

    with op.batch_alter_table("saved_schedules") as batch_op:
        batch_op.add_column(sa.Column("workspace_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_saved_schedules_workspace_id", ["workspace_id"])
        batch_op.create_foreign_key("fk_saved_schedules_workspace", "workspaces", ["workspace_id"], ["id"])

def downgrade() -> None:
    with op.batch_alter_table("saved_schedules") as batch_op:
        batch_op.drop_constraint("fk_saved_schedules_workspace", type_="foreignkey")
        batch_op.drop_index("ix_saved_schedules_workspace_id")
        batch_op.drop_column("workspace_id")

    with op.batch_alter_table("class_matter_assignments") as batch_op:
        batch_op.drop_constraint("fk_class_matter_assignments_workspace", type_="foreignkey")
        batch_op.drop_index("ix_class_matter_assignments_workspace_id")
        batch_op.drop_column("workspace_id")

    with op.batch_alter_table("matters") as batch_op:
        batch_op.drop_constraint("uq_workspace_matter_name", type_="unique")
        batch_op.drop_constraint("fk_matters_workspace", type_="foreignkey")
        batch_op.drop_index("ix_matters_workspace_id")
        batch_op.drop_column("workspace_id")

    with op.batch_alter_table("classes") as batch_op:
        batch_op.drop_constraint("uq_workspace_class", type_="unique")
        batch_op.drop_constraint("fk_classes_workspace", type_="foreignkey")
        batch_op.drop_index("ix_classes_workspace_id")
        batch_op.drop_column("workspace_id")

    with op.batch_alter_table("teacher_unavailabilities") as batch_op:
        batch_op.drop_constraint("uq_teacher_unavailability_slot", type_="unique")
        batch_op.drop_constraint("fk_teacher_unavailabilities_workspace", type_="foreignkey")
        batch_op.drop_index("ix_teacher_unavailabilities_workspace_id")
        batch_op.drop_column("workspace_id")

    with op.batch_alter_table("teachers") as batch_op:
        batch_op.drop_constraint("fk_teachers_workspace", type_="foreignkey")
        batch_op.drop_index("ix_teachers_workspace_id")
        batch_op.drop_column("workspace_id")

    op.drop_table("auth_sessions")
    op.drop_table("workspace_memberships")
    op.drop_table("workspaces")
    op.drop_table("users")
