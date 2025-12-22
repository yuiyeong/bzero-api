"""0012 Create Diary

Revision ID: 712a85aaef6b
Revises: d2c76d767f7e
Create Date: 2025-12-22 17:39:36.803451

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "712a85aaef6b"
down_revision: str | Sequence[str] | None = "d2c76d767f7e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "diaries",
        sa.Column("diary_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("room_stay_id", sa.UUID(), nullable=False),
        sa.Column("city_id", sa.UUID(), nullable=False),
        sa.Column("guest_house_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("mood", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["city_id"], ["cities.city_id"]),
        sa.ForeignKeyConstraint(["guest_house_id"], ["guest_houses.guest_house_id"]),
        sa.ForeignKeyConstraint(["room_stay_id"], ["room_stays.room_stay_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("diary_id"),
    )
    op.create_index(
        "uq_diaries_room_stay_id_active",
        "diaries",
        ["room_stay_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # update_updated_at_column() 함수는 0001_create_user.py에서 이미 생성됨
    op.execute("""
    CREATE TRIGGER update_diaries_updated_at
       BEFORE UPDATE
       ON diaries
       FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_diaries_updated_at ON diaries;")

    op.drop_index(
        "uq_diaries_room_stay_id_active", table_name="diaries", postgresql_where=sa.text("deleted_at IS NULL")
    )
    op.drop_table("diaries")
