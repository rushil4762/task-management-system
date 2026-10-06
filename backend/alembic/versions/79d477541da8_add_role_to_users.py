"""add_role_to_users

Revision ID: 79d477541da8
Revises: ca7f66f3ea66
Create Date: 2026-10-01 07:17:47.455161

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79d477541da8'
down_revision: Union[str, Sequence[str], None] = 'ca7f66f3ea66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add role enum and column to users table."""
    userrole_enum = sa.Enum('CEO', 'EMPLOYEE', name='userrole')
    userrole_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'users',
        sa.Column(
            'role',
            userrole_enum,
            server_default='EMPLOYEE',
            nullable=False,
        ),
    )
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)


def downgrade() -> None:
    """Downgrade schema: remove role column and enum from users table."""
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_column('users', 'role')
    userrole_enum = sa.Enum('CEO', 'EMPLOYEE', name='userrole')
    userrole_enum.drop(op.get_bind(), checkfirst=True)
