"""add_task_comments_and_activities

Revision ID: e5a87b32c109
Revises: 0ba741ab35f1
Create Date: 2026-09-29 09:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5a87b32c109'
down_revision: Union[str, Sequence[str], None] = '0ba741ab35f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add task_comments and task_activities tables."""
    # 1. Create task_comments table
    op.create_table(
        'task_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_comments_id'), 'task_comments', ['id'], unique=False)
    op.create_index(op.f('ix_task_comments_task_id'), 'task_comments', ['task_id'], unique=False)
    op.create_index(op.f('ix_task_comments_user_id'), 'task_comments', ['user_id'], unique=False)

    # 2. Create task_activities table
    op.create_table(
        'task_activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_activities_id'), 'task_activities', ['id'], unique=False)
    op.create_index(op.f('ix_task_activities_task_id'), 'task_activities', ['task_id'], unique=False)
    op.create_index(op.f('ix_task_activities_user_id'), 'task_activities', ['user_id'], unique=False)
    op.create_index(op.f('ix_task_activities_created_at'), 'task_activities', ['created_at'], unique=False)
    op.create_index('ix_task_activities_task_created', 'task_activities', ['task_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema: drop task_activities and task_comments tables."""
    op.drop_index('ix_task_activities_task_created', table_name='task_activities')
    op.drop_index(op.f('ix_task_activities_created_at'), table_name='task_activities')
    op.drop_index(op.f('ix_task_activities_user_id'), table_name='task_activities')
    op.drop_index(op.f('ix_task_activities_task_id'), table_name='task_activities')
    op.drop_index(op.f('ix_task_activities_id'), table_name='task_activities')
    op.drop_table('task_activities')

    op.drop_index(op.f('ix_task_comments_user_id'), table_name='task_comments')
    op.drop_index(op.f('ix_task_comments_task_id'), table_name='task_comments')
    op.drop_index(op.f('ix_task_comments_id'), table_name='task_comments')
    op.drop_table('task_comments')
