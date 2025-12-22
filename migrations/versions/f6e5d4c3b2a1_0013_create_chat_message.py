"""0013 Create ChatMessage

Revision ID: f6e5d4c3b2a1
Revises: a1b2c3d4e5f6
Create Date: 2025-12-17 11:00:01.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f6e5d4c3b2a1"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "chat_messages",
        sa.Column("message_id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("card_id", sa.UUID(), nullable=True),
        sa.Column("message_type", sa.String(length=20), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["card_id"],
            ["conversation_cards.card_id"],
        ),
        sa.ForeignKeyConstraint(
            ["room_id"],
            ["rooms.room_id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("message_id"),
    )

    # 인덱스 생성
    op.create_index(
        "idx_chat_messages_room_created",
        "chat_messages",
        ["room_id", "created_at"],
    )

    op.create_index(
        "idx_chat_messages_expires",
        "chat_messages",
        ["expires_at"],
    )

    # update_updated_at_column() 함수는 0001_create_user.py에서 이미 생성됨
    op.execute("""
    CREATE TRIGGER update_chat_messages_updated_at
       BEFORE UPDATE
       ON chat_messages
       FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_chat_messages_updated_at ON chat_messages;")

    # Drop indexes
    op.drop_index("idx_chat_messages_expires", table_name="chat_messages")
    op.drop_index("idx_chat_messages_room_created", table_name="chat_messages")

    op.drop_table("chat_messages")
