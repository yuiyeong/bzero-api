from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class RoomModel(Base, AuditMixin, SoftDeleteMixin):
    """Room SQLAlchemy 모델.

    Room 도메인 엔티티의 영속성을 담당하는 ORM 모델입니다.
    여행자들이 체류하고 대화하는 동적 공간을 테이블로 매핑합니다.

    Columns:
        room_id: PK, UUID v7
        guest_house_id: FK → guest_houses.guest_house_id
        max_capacity: 최대 수용 인원 (기본 6명)
        current_capacity: 현재 체류 중인 여행자 수

    Mixins:
        AuditMixin: created_at, updated_at 자동 관리
        SoftDeleteMixin: deleted_at을 통한 soft delete 지원
    """

    __tablename__ = "rooms"

    room_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    guest_house_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("guest_houses.guest_house_id"), nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    current_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
