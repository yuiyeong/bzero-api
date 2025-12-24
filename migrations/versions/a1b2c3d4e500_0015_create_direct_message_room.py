"""Create direct_message_rooms table.

Revision ID: 0015_create_direct_message_room
Revises: fd76fc635285
Create Date: 2025-12-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e500"
down_revision: str | None = "fd76fc635285"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create direct_message_rooms table with indexes and constraints."""
    op.create_table(
        "direct_message_rooms",
        sa.Column("dm_room_id", sa.UUID(), nullable=False),
        sa.Column("guesthouse_id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("user1_id", sa.UUID(), nullable=False),
        sa.Column("user2_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("dm_room_id"),
        sa.ForeignKeyConstraint(
            ["guesthouse_id"],
            ["guest_houses.guest_house_id"],
        ),
        sa.ForeignKeyConstraint(
            ["room_id"],
            ["rooms.room_id"],
        ),
        sa.ForeignKeyConstraint(
            ["user1_id"],
            ["users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["user2_id"],
            ["users.user_id"],
        ),
    )

    # 인덱스 생성
    op.create_index(
        "idx_dm_rooms_room_status",
        "direct_message_rooms",
        ["room_id", "status"],
    )
    op.create_index(
        "idx_dm_rooms_guesthouse_status",
        "direct_message_rooms",
        ["guesthouse_id", "status"],
    )
    op.create_index(
        "idx_dm_rooms_user2_status",
        "direct_message_rooms",
        ["user2_id", "status"],
    )

    # 중복 신청 방지 Unique 제약 (Partial)
    op.create_index(
        "uq_dm_rooms_room_users_partial",
        "direct_message_rooms",
        ["room_id", "user1_id", "user2_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND status NOT IN ('rejected', 'ended')"),
    )


def downgrade() -> None:
    """Drop direct_message_rooms table and indexes."""
    op.drop_index("uq_dm_rooms_room_users_partial", table_name="direct_message_rooms")
    op.drop_index("idx_dm_rooms_user2_status", table_name="direct_message_rooms")
    op.drop_index("idx_dm_rooms_guesthouse_status", table_name="direct_message_rooms")
    op.drop_index("idx_dm_rooms_room_status", table_name="direct_message_rooms")
    op.drop_table("direct_message_rooms")
