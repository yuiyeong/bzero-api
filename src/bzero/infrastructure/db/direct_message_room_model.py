"""DirectMessageRoom ORM 모델.

1:1 대화방 도메인 엔티티의 영속성을 담당합니다.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.domain.entities.direct_message_room import DirectMessageRoom
from bzero.domain.value_objects import DMStatus, Id
from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class DirectMessageRoomModel(Base, AuditMixin, SoftDeleteMixin):
    """DirectMessageRoom SQLAlchemy 모델.

    DirectMessageRoom 도메인 엔티티의 영속성을 담당하는 ORM 모델입니다.

    Columns:
        dm_room_id: PK, UUID v7
        guesthouse_id: FK → guest_houses.guest_house_id
        room_id: FK → rooms.room_id (같은 룸 검증 기준)
        requester_id: FK → users.user_id (대화 신청자)
        receiver_id: FK → users.user_id (대화 수신자)
        status: 대화방 상태 (pending, accepted, active, rejected, ended)
        started_at: 대화 시작 시간 (ACCEPTED 시 기록)
        ended_at: 대화 종료 시간 (ENDED 시 기록)

    Mixins:
        AuditMixin: created_at, updated_at 자동 관리
        SoftDeleteMixin: deleted_at을 통한 soft delete 지원
    """

    __tablename__ = "direct_message_rooms"

    dm_room_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    guesthouse_id: Mapped[UUID] = mapped_column(
        UUID, ForeignKey("guest_houses.guest_house_id"), nullable=False
    )
    room_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("rooms.room_id"), nullable=False)
    requester_id: Mapped[UUID] = mapped_column(
        UUID, ForeignKey("users.user_id"), nullable=False
    )
    receiver_id: Mapped[UUID] = mapped_column(
        UUID, ForeignKey("users.user_id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # 인덱스: 룸별 상태 조회
        Index("idx_dm_rooms_room_status", "room_id", "status"),
        # 인덱스: 게스트하우스별 상태 조회
        Index("idx_dm_rooms_guesthouse_status", "guesthouse_id", "status"),
        # 인덱스: receiver별 상태 조회 (대화 신청 알림용)
        Index("idx_dm_rooms_receiver_status", "receiver_id", "status"),
        # 중복 신청 방지: 같은 룸에서 같은 두 사용자 간에는 하나의 활성 대화방만 존재
        UniqueConstraint(
            "room_id",
            "requester_id",
            "receiver_id",
            name="uq_dm_rooms_room_users",
        ),
    )


