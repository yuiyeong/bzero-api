"""0010 Create Room

Revision ID: b6530ca16627
Revises: 7914a808fe83
Create Date: 2025-12-11 20:00:45.669934

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b6530ca16627"
down_revision: str | Sequence[str] | None = "7914a808fe83"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "rooms",
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("guest_house_id", sa.UUID(), nullable=False),
        sa.Column("max_capacity", sa.Integer(), nullable=False),
        sa.Column("current_capacity", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["guest_house_id"],
            ["guest_houses.guest_house_id"],
        ),
        sa.PrimaryKeyConstraint("room_id"),
    )

    # update_updated_at_column() 함수는 0001_create_user.py에서 이미 생성됨
    op.execute("""
        CREATE TRIGGER update_rooms_updated_at
           BEFORE UPDATE
           ON rooms
           FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_rooms_updated_at ON rooms;")

    op.drop_table("rooms")
