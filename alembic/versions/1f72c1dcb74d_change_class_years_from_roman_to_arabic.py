"""change class years from roman to arabic

Revision ID: 1f72c1dcb74d
Revises: 72e1f73d9a4c
Create Date: 2026-09-12 22:46:05.824564

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f72c1dcb74d'
down_revision: Union[str, Sequence[str], None] = '72e1f73d9a4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE classes
        SET year = CASE year
            WHEN 'I' THEN '1'
            WHEN 'II' THEN '2'
            WHEN 'III' THEN '3'
            WHEN 'IV' THEN '4'
            WHEN 'V' THEN '5'
            ELSE year
        END
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE classes
        SET year = CASE year
            WHEN '1' THEN 'I'
            WHEN '2' THEN 'II'
            WHEN '3' THEN 'III'
            WHEN '4' THEN 'IV'
            WHEN '5' THEN 'V'
            ELSE year
        END
    """)
