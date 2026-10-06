"""add_metadata_to_task_activities

Revision ID: d4e1f2a3b4c5
Revises: 79d477541da8
Create Date: 2026-10-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e1f2a3b4c5'
down_revision: Union[str, Sequence[str], None] = '79d477541da8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add metadata column to task_activities table."""
    op.add_column(
        'task_activities',
        sa.Column('metadata', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Drop metadata column from task_activities table."""
    op.drop_column('task_activities', 'metadata')
