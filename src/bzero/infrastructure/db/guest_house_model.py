from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class GuestHouseModel(Base, AuditMixin, SoftDeleteMixin):
    """GuestHouse SQLAlchemy 모델.

    GuestHouse 도메인 엔티티의 영속성을 담당하는 ORM 모델입니다.
    도시에 있는 영구적인 숙소 컨테이너를 테이블로 매핑합니다.

    Columns:
        guest_house_id: PK, UUID v7
        city_id: FK → cities.city_id
        guest_house_type: GuestHouse 타입 (MIXED, QUIET)
        name: GuestHouse 이름 (최대 100자)
        description: GuestHouse 설명
        image_url: GuestHouse 이미지 URL (최대 500자)
        is_active: 활성화 상태

    Mixins:
        AuditMixin: created_at, updated_at 자동 관리
        SoftDeleteMixin: deleted_at을 통한 soft delete 지원
    """

    __tablename__ = "guest_houses"

    guest_house_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    city_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("cities.city_id"), nullable=False)
    guest_house_type: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=False, nullable=False)
