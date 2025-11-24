"""Remove phase column from cities table

Revision ID: b2373b2f3b2e
Revises: 019aa594c20e
Create Date: 2025-11-24 10:27:27.592230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2373b2f3b2e'
down_revision: Union[str, Sequence[str], None] = '019aa594c20e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the phase index
    op.drop_index("idx_cities_phase", table_name="cities")

    # Drop the phase column
    op.drop_column("cities", "phase")


def downgrade() -> None:
    """Downgrade schema."""
    # Add back the phase column
    op.add_column(
        "cities",
        sa.Column("phase", sa.Integer(), nullable=False, server_default=sa.text("1"))
    )

    # Recreate the phase index
    op.create_index(
        index_name="idx_cities_phase",
        table_name="cities",
        columns=["phase"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
