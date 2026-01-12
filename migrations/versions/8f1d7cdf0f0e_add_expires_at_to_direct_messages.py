"""add expires_at to direct_messages

Revision ID: 8f1d7cdf0f0e
Revises: c3e986d003cc
Create Date: 2026-01-12 18:19:59.256014

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f1d7cdf0f0e'
down_revision: Union[str, Sequence[str], None] = 'c3e986d003cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('direct_messages', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        'idx_direct_messages_expires',
        'direct_messages',
        ['expires_at'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_direct_messages_expires', table_name='direct_messages')
    op.drop_column('direct_messages', 'expires_at')
