"""0012 Create ConversationCard

Revision ID: a1b2c3d4e5f6
Revises: d2c76d767f7e
Create Date: 2025-12-17 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "d2c76d767f7e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "conversation_cards",
        sa.Column("card_id", sa.UUID(), nullable=False),
        sa.Column("city_id", sa.UUID(), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.PrimaryKeyConstraint("card_id"),
    )

    # 인덱스 생성
    op.create_index(
        "idx_conversation_cards_city_active",
        "conversation_cards",
        ["city_id", "is_active"],
    )

    # update_updated_at_column() 함수는 0001_create_user.py에서 이미 생성됨
    op.execute("""
    CREATE TRIGGER update_conversation_cards_updated_at
       BEFORE UPDATE
       ON conversation_cards
       FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_conversation_cards_updated_at ON conversation_cards;")

    # Drop index
    op.drop_index("idx_conversation_cards_city_active", table_name="conversation_cards")

    op.drop_table("conversation_cards")
