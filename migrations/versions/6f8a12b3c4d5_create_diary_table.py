"""Create diary table

Revision ID: 6f8a12b3c4d5
Revises: 9b94381f2c77
Create Date: 2025-12-08 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6f8a12b3c4d5'
down_revision: Union[str, Sequence[str], None] = '9b94381f2c77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'diaries',
        sa.Column('diary_id', postgresql.UUID(), nullable=False),
        sa.Column('user_id', postgresql.UUID(), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('mood', sa.String(length=10), nullable=False),
        sa.Column('diary_date', sa.Date(), nullable=False),
        sa.Column('city_id', postgresql.UUID(), nullable=True),
        sa.Column('has_earned_points', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name='fk_diaries_user_id'),
        sa.ForeignKeyConstraint(['city_id'], ['cities.city_id'], name='fk_diaries_city_id'),
        sa.PrimaryKeyConstraint('diary_id'),
        sa.UniqueConstraint('user_id', 'diary_date', name='uq_diaries_user_id_diary_date')
    )
    op.create_index('idx_diaries_user_id_diary_date', 'diaries', ['user_id', 'diary_date'], unique=False)
    op.create_index('idx_diaries_user_id', 'diaries', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_diaries_user_id', table_name='diaries')
    op.drop_index('idx_diaries_user_id_diary_date', table_name='diaries')
    op.drop_table('diaries')
