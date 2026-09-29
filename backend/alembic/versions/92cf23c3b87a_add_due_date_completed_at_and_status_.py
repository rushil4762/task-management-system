"""add_due_date_completed_at_and_status_priority_enhancements

Revision ID: 92cf23c3b87a
Revises: abb3f6578613
Create Date: 2026-09-28 07:13:17.196558

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92cf23c3b87a'
down_revision: Union[str, Sequence[str], None] = 'abb3f6578613'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add due_date, completed_at, new enum values, and targeted indexes."""
    bind = op.get_bind()
    # If running against PostgreSQL, add new enum values safely
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS 'CANCELLED'")
        op.execute("ALTER TYPE taskpriority ADD VALUE IF NOT EXISTS 'URGENT'")

    # Add columns to tasks table
    op.add_column('tasks', sa.Column('due_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('tasks', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))

    # Add single-column indexes
    op.create_index(op.f('ix_tasks_due_date'), 'tasks', ['due_date'], unique=False)
    op.create_index(op.f('ix_tasks_completed_at'), 'tasks', ['completed_at'], unique=False)

    # Add composite indexes for common user queries
    op.create_index('ix_tasks_user_status', 'tasks', ['user_id', 'status'], unique=False)
    op.create_index('ix_tasks_user_due_date', 'tasks', ['user_id', 'due_date'], unique=False)
    op.create_index('ix_tasks_user_created_at', 'tasks', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema: drop indexes and added columns."""
    op.drop_index('ix_tasks_user_created_at', table_name='tasks')
    op.drop_index('ix_tasks_user_due_date', table_name='tasks')
    op.drop_index('ix_tasks_user_status', table_name='tasks')
    op.drop_index(op.f('ix_tasks_completed_at'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_due_date'), table_name='tasks')
    op.drop_column('tasks', 'completed_at')
    op.drop_column('tasks', 'due_date')
