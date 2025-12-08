"""0008 Add base_cost_points and base_duration_hours to cities

Revision ID: 0512ec73b9ed
Revises: 442b2cf6617e
Create Date: 2025-12-08 20:53:43.732958

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0512ec73b9ed'
down_revision: Union[str, Sequence[str], None] = '442b2cf6617e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
