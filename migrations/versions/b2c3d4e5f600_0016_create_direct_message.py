"""Create direct_messages table.

Revision ID: 0016_create_direct_message
Revises: a1b2c3d4e500
Create Date: 2025-12-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f600"
down_revision: str | None = "a1b2c3d4e500"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create direct_messages table with indexes."""
    op.create_table(
        "direct_messages",
        sa.Column("dm_id", sa.UUID(), nullable=False),
        sa.Column("dm_room_id", sa.UUID(), nullable=False),
        sa.Column("from_user_id", sa.UUID(), nullable=False),
        sa.Column("to_user_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
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
        sa.PrimaryKeyConstraint("dm_id"),
        sa.ForeignKeyConstraint(
            ["dm_room_id"],
            ["direct_message_rooms.dm_room_id"],
        ),
        sa.ForeignKeyConstraint(
            ["from_user_id"],
            ["users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["to_user_id"],
            ["users.user_id"],
        ),
    )

    # 인덱스 생성
    op.create_index(
        "idx_dm_messages_room_created",
        "direct_messages",
        ["dm_room_id", "created_at"],
    )
    op.create_index(
        "idx_dm_messages_to_user_read",
        "direct_messages",
        ["to_user_id", "is_read"],
    )


def downgrade() -> None:
    """Drop direct_messages table and indexes."""
    op.drop_index("idx_dm_messages_to_user_read", table_name="direct_messages")
    op.drop_index("idx_dm_messages_room_created", table_name="direct_messages")
    op.drop_table("direct_messages")
