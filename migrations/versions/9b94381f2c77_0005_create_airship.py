"""0005 Create Airship

Revision ID: 9b94381f2c77
Revises: 282e91370e30
Create Date: 2025-12-05 17:46:32.045808

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9b94381f2c77"
down_revision: str | Sequence[str] | None = "282e91370e30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "airships",
        sa.Column("airship_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("cost_factor", sa.Integer(), nullable=False),
        sa.Column("duration_factor", sa.Integer(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("airship_id"),
    )
    op.create_index(
        "idx_airships_active_display_order",
        "airships",
        ["is_active", "display_order"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # update_updated_at_column() 함수는 0001_create_user.py에서 이미 생성됨
    op.execute("""
    CREATE TRIGGER update_airships_updated_at
       BEFORE UPDATE ON airships
       FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_airships_updated_at ON airships;")

    op.drop_index(
        "idx_airships_active_display_order", table_name="airships", postgresql_where=sa.text("deleted_at IS NULL")
    )
    op.drop_table("airships")
