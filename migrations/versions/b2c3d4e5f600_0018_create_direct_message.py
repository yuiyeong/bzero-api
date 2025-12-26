"""0018 Create Direct Message (Consolidated)

Revision ID: b2c3d4e5f600
Revises: a1b2c3d4e500
Create Date: 2025-12-26
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f600"
down_revision: str | None = "a1b2c3d4e500"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create direct_messages table."""
    op.create_table(
        "direct_messages",
        sa.Column("dm_id", sa.UUID(), nullable=False),
        sa.Column("dm_room_id", sa.UUID(), nullable=False),
        sa.Column("from_user_id", sa.UUID(), nullable=False),
        sa.Column("to_user_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
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
            ondelete="CASCADE",
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

    # updated_at 트리거 연결
    op.execute("""
    CREATE TRIGGER update_direct_messages_updated_at
        BEFORE UPDATE ON direct_messages
        FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop direct_messages table."""
    op.execute("DROP TRIGGER IF EXISTS update_direct_messages_updated_at ON direct_messages;")
    
    op.drop_index("idx_dm_messages_to_user_read", table_name="direct_messages")
    op.drop_index("idx_dm_messages_room_created", table_name="direct_messages")
    op.drop_table("direct_messages")
