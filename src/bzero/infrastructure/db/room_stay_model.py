from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class RoomStayModel(Base, AuditMixin, SoftDeleteMixin):
    """RoomStay SQLAlchemy 모델.

    RoomStay 도메인 엔티티의 영속성을 담당하는 ORM 모델입니다.
    개별 여행자의 체류 기록을 테이블로 매핑합니다.

    Columns:
        room_stay_id: PK, UUID v7
        user_id: FK → users.user_id (여행자)
        city_id: FK → cities.city_id (도시)
        guest_house_id: FK → guest_houses.guest_house_id (게스트하우스)
        room_id: FK → rooms.room_id (룸)
        ticket_id: FK → tickets.ticket_id (체크인에 사용된 티켓)
        status: 체류 상태 (CHECKED_IN, CHECKED_OUT, EXTENDED)
        check_in_at: 체크인 시각 (timezone aware)
        scheduled_check_out_at: 예정 체크아웃 시각 (timezone aware)
        actual_check_out_at: 실제 체크아웃 시각 (nullable, timezone aware)
        extension_count: 연장 횟수 (기본값 0)

    Mixins:
        AuditMixin: created_at, updated_at 자동 관리
        SoftDeleteMixin: deleted_at을 통한 soft delete 지원
    """

    __tablename__ = "room_stays"

    room_stay_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.user_id"), nullable=False)
    city_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("cities.city_id"), nullable=False)
    guest_house_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("guest_houses.guest_house_id"), nullable=False)
    room_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("rooms.room_id"), nullable=False)
    ticket_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("tickets.ticket_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    check_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_check_out_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_check_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    extension_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
