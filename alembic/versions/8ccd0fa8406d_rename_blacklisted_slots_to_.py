"""rename_blacklisted_slots_to_unavailabilities

Revision ID: 8ccd0fa8406d
Revises: d687bd85b9d6
Create Date: 2026-07-30 17:49:01.189341

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ccd0fa8406d'
down_revision: Union[str, Sequence[str], None] = 'd687bd85b9d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table("teacher_blacklisted_slots", "teacher_unavailabilities")


def downgrade() -> None:
    """Downgrade schema."""
    op.rename_table("teacher_unavailabilities", "teacher_blacklisted_slots")
