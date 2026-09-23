"""add class color

Revision ID: b4c2e8f1a7d3
Revises: 1f72c1dcb74d
Create Date: 2026-09-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b4c2e8f1a7d3"
down_revision: Union[str, Sequence[str], None] = "1f72c1dcb74d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Frozen copy of squola.models.CLASS_COLOR_PALETTE at the time of this migration.
PALETTE = [
    "#f5bcbc", "#f5debc", "#eaf5bc", "#c8f5bc", "#bcf5d3", "#bcf5f5", "#bcd3f5", "#c8bcf5", "#eabcf5", "#f5bcde",
    "#efac8f", "#efe58f", "#bfef8f", "#8fef99", "#8fefd2", "#8fd2ef", "#8f99ef", "#bf8fef", "#ef8fe6", "#ef8fac",
    "#fae0db", "#faf2db", "#effadb", "#ddfadb", "#dbfaec", "#dbf5fa", "#dbe3fa", "#e6dbfa", "#f8dbfa", "#fadbe9",
]


def upgrade() -> None:
    with op.batch_alter_table("classes") as batch_op:
        batch_op.add_column(sa.Column("color", sa.String(length=7), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, workspace_id FROM classes ORDER BY workspace_id, id")).all()
    position: dict[int, int] = {}
    for class_id, workspace_id in rows:
        index = position.get(workspace_id, 0)
        position[workspace_id] = index + 1
        conn.execute(
            sa.text("UPDATE classes SET color = :color WHERE id = :id"),
            {"color": PALETTE[index % len(PALETTE)], "id": class_id},
        )

    with op.batch_alter_table("classes") as batch_op:
        batch_op.alter_column("color", existing_type=sa.String(length=7), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("classes") as batch_op:
        batch_op.drop_column("color")
