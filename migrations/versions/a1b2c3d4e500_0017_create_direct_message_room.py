"""0017 Create Direct Message Room (Consolidated)

Revision ID: a1b2c3d4e500
Revises: 6ded77394e5c
Create Date: 2025-12-26
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e500"
down_revision: str | None = "6ded77394e5c"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create direct_message_rooms table with correct schema and triggers."""
    op.create_table(
        "direct_message_rooms",
        sa.Column("dm_room_id", sa.UUID(), nullable=False),
        sa.Column("guesthouse_id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("requester_id", sa.UUID(), nullable=False),
        sa.Column("receiver_id", sa.UUID(), nullable=False),
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
            ["requester_id"],
            ["users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["receiver_id"],
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
        "idx_dm_rooms_receiver_status",  # receiver 기준 조회 최적화
        "direct_message_rooms",
        ["receiver_id", "status"],
    )

    # 중복 신청 방지 Unique 제약 (Partial Index)
    # 삭제되지 않고, 거절/종료되지 않은 상태에서 동일 룸, 동일 신청자/수신자 조합 유일
    op.create_index(
        "uq_dm_rooms_room_users_partial",
        "direct_message_rooms",
        ["room_id", "requester_id", "receiver_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND status NOT IN ('rejected', 'ended')"),
    )

    # updated_at 트리거 연결 (0001_create_user.py에서 생성된 함수 사용)
    op.execute("""
    CREATE TRIGGER update_direct_message_rooms_updated_at
        BEFORE UPDATE ON direct_message_rooms
        FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop direct_message_rooms table."""
    # 트리거 삭제
    op.execute("DROP TRIGGER IF EXISTS update_direct_message_rooms_updated_at ON direct_message_rooms;")

    op.drop_index("uq_dm_rooms_room_users_partial", table_name="direct_message_rooms")
    op.drop_index("idx_dm_rooms_receiver_status", table_name="direct_message_rooms")
    op.drop_index("idx_dm_rooms_guesthouse_status", table_name="direct_message_rooms")
    op.drop_index("idx_dm_rooms_room_status", table_name="direct_message_rooms")
    op.drop_table("direct_message_rooms")
