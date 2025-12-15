"""0011 Create RoomStay

Revision ID: d2c76d767f7e
Revises: b6530ca16627
Create Date: 2025-12-12 19:00:24.263867

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d2c76d767f7e"
down_revision: str | Sequence[str] | None = "b6530ca16627"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "room_stays",
        sa.Column("room_stay_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("city_id", sa.UUID(), nullable=False),
        sa.Column("guest_house_id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("ticket_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("check_in_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_check_out_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_check_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extension_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["city_id"],
            ["cities.city_id"],
        ),
        sa.ForeignKeyConstraint(
            ["guest_house_id"],
            ["guest_houses.guest_house_id"],
        ),
        sa.ForeignKeyConstraint(
            ["room_id"],
            ["rooms.room_id"],
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.ticket_id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("room_stay_id"),
    )

    # update_updated_at_column() 함수는 0001_create_user.py에서 이미 생성됨
    op.execute("""
    CREATE TRIGGER update_room_stays_updated_at
       BEFORE UPDATE
       ON room_stays
       FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_room_stays_updated_at ON room_stays;")

    op.drop_table("room_stays")
