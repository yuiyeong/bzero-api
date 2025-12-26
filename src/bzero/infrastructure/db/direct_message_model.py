"""DirectMessage ORM 모델.

1:1 대화 메시지 도메인 엔티티의 영속성을 담당합니다.
"""

from sqlalchemy import Boolean, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class DirectMessageModel(Base, AuditMixin, SoftDeleteMixin):
    """DirectMessage SQLAlchemy 모델.

    DirectMessage 도메인 엔티티의 영속성을 담당하는 ORM 모델입니다.

    Columns:
        dm_id: PK, UUID v7
        dm_room_id: FK → direct_message_rooms.dm_room_id
        from_user_id: FK → users.user_id (발신자)
        to_user_id: FK → users.user_id (수신자)
        content: 메시지 내용 (최대 300자)
        is_read: 읽음 여부

    Mixins:
        AuditMixin: created_at, updated_at 자동 관리
        SoftDeleteMixin: deleted_at을 통한 soft delete 지원
    """

    __tablename__ = "direct_messages"

    dm_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    dm_room_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("direct_message_rooms.dm_room_id"), nullable=False)
    from_user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.user_id"), nullable=False)
    to_user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.user_id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        # 인덱스: 대화방별 메시지 조회 (시간순, Soft Delete 제외)
        Index(
            "idx_dm_messages_room_created",
            "dm_room_id",
            "created_at",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        # 인덱스: 수신자별 읽지 않은 메시지 조회 (Soft Delete 제외)
        Index(
            "idx_dm_messages_to_user_read",
            "to_user_id",
            "is_read",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
