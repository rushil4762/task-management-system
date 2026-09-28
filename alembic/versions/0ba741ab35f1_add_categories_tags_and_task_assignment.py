"""add_categories_tags_and_task_assignment

Revision ID: 0ba741ab35f1
Revises: 92cf23c3b87a
Create Date: 2026-09-28 07:51:44.690907

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ba741ab35f1'
down_revision: Union[str, Sequence[str], None] = '92cf23c3b87a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add categories, tags, task_tags association table, and task assignment/category columns."""
    # 1. Create categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_categories_user_name'),
    )
    op.create_index(op.f('ix_categories_id'), 'categories', ['id'], unique=False)
    op.create_index(op.f('ix_categories_user_id'), 'categories', ['user_id'], unique=False)

    # 2. Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_tags_user_name'),
    )
    op.create_index(op.f('ix_tags_id'), 'tags', ['id'], unique=False)
    op.create_index(op.f('ix_tags_user_id'), 'tags', ['user_id'], unique=False)

    # 3. Create task_tags association table
    op.create_table(
        'task_tags',
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('task_id', 'tag_id'),
    )
    op.create_index(op.f('ix_task_tags_task_id'), 'task_tags', ['task_id'], unique=False)
    op.create_index(op.f('ix_task_tags_tag_id'), 'task_tags', ['tag_id'], unique=False)

    # 4. Add category_id and assigned_to_id to tasks table
    op.add_column('tasks', sa.Column('category_id', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column('assigned_to_id', sa.Integer(), nullable=True))

    op.create_index(op.f('ix_tasks_category_id'), 'tasks', ['category_id'], unique=False)
    op.create_index(op.f('ix_tasks_assigned_to_id'), 'tasks', ['assigned_to_id'], unique=False)
    op.create_index('ix_tasks_user_category', 'tasks', ['user_id', 'category_id'], unique=False)
    op.create_index('ix_tasks_assigned_status', 'tasks', ['assigned_to_id', 'status'], unique=False)

    op.create_foreign_key(
        'fk_tasks_category_id_categories',
        'tasks',
        'categories',
        ['category_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_tasks_assigned_to_id_users',
        'tasks',
        'users',
        ['assigned_to_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema: remove foreign keys, columns, and organization tables."""
    op.drop_constraint('fk_tasks_assigned_to_id_users', 'tasks', type_='foreignkey')
    op.drop_constraint('fk_tasks_category_id_categories', 'tasks', type_='foreignkey')

    op.drop_index('ix_tasks_assigned_status', table_name='tasks')
    op.drop_index('ix_tasks_user_category', table_name='tasks')
    op.drop_index(op.f('ix_tasks_assigned_to_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_category_id'), table_name='tasks')

    op.drop_column('tasks', 'assigned_to_id')
    op.drop_column('tasks', 'category_id')

    op.drop_index(op.f('ix_task_tags_tag_id'), table_name='task_tags')
    op.drop_index(op.f('ix_task_tags_task_id'), table_name='task_tags')
    op.drop_table('task_tags')

    op.drop_index(op.f('ix_tags_user_id'), table_name='tags')
    op.drop_index(op.f('ix_tags_id'), table_name='tags')
    op.drop_table('tags')

    op.drop_index(op.f('ix_categories_user_id'), table_name='categories')
    op.drop_index(op.f('ix_categories_id'), table_name='categories')
    op.drop_table('categories')
