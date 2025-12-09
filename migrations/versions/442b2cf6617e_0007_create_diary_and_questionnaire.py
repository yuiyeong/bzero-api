"""0007 Create diary and questionnaire

Revision ID: 442b2cf6617e
Revises: d07e6829dd95
Create Date: 2025-12-08 20:50:19.819266

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '442b2cf6617e'
down_revision: Union[str, Sequence[str], None] = 'd07e6829dd95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create diaries table
    op.create_table('diaries',
    sa.Column('diary_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=True),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('mood', sa.String(length=10), nullable=False),
    sa.Column('diary_date', sa.Date(), nullable=False),
    sa.Column('city_id', sa.UUID(), nullable=True),
    sa.Column('has_earned_points', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['city_id'], ['cities.city_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('diary_id'),
    sa.UniqueConstraint('user_id', 'diary_date', name='uq_diaries_user_id_diary_date')
    )
    op.create_index(op.f('ix_diaries_diary_date'), 'diaries', ['diary_date'], unique=False)
    op.create_index(op.f('ix_diaries_user_id'), 'diaries', ['user_id'], unique=False)

    # Create questionnaires table
    op.create_table('questionnaires',
    sa.Column('questionnaire_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('city_id', sa.UUID(), nullable=False),
    sa.Column('question_1_answer', sa.String(length=200), nullable=False),
    sa.Column('question_2_answer', sa.String(length=200), nullable=False),
    sa.Column('question_3_answer', sa.String(length=200), nullable=False),
    sa.Column('has_earned_points', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['city_id'], ['cities.city_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('questionnaire_id'),
    sa.UniqueConstraint('user_id', 'city_id', name='uq_questionnaires_user_id_city_id')
    )
    op.create_index(op.f('ix_questionnaires_city_id'), 'questionnaires', ['city_id'], unique=False)
    op.create_index(op.f('ix_questionnaires_user_id'), 'questionnaires', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_questionnaires_user_id'), table_name='questionnaires')
    op.drop_index(op.f('ix_questionnaires_city_id'), table_name='questionnaires')
    op.drop_table('questionnaires')
    op.drop_index(op.f('ix_diaries_user_id'), table_name='diaries')
    op.drop_index(op.f('ix_diaries_diary_date'), table_name='diaries')
    op.drop_table('diaries')
