"""add roomstays_id to chat_messages

Revision ID: c3e986d003cc
Revises: 18eb37daa3a2
Create Date: 2026-01-12 15:46:43.156760

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3e986d003cc'
down_revision: Union[str, Sequence[str], None] = '18eb37daa3a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("chat_messages", sa.Column("roomstays_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_chat_messages_roomstays_id_room_stays",
        "chat_messages",
        "room_stays",
        ["roomstays_id"],
        ["room_stay_id"],
    )
    op.create_index(
        "idx_chat_messages_roomstays_id_is_system",
        "chat_messages",
        ["roomstays_id", "is_system"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_chat_messages_roomstays_id_is_system", table_name="chat_messages")
    op.drop_constraint("fk_chat_messages_roomstays_id_room_stays", "chat_messages", type_="foreignkey")
    op.drop_column("chat_messages", "roomstays_id")
