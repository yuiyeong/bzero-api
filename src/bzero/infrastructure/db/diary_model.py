from sqlalchemy import ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class DiaryModel(Base, AuditMixin, SoftDeleteMixin):
    """Diary SQLAlchemy 모델.

    Diary 도메인 엔티티의 영속성을 담당하는 ORM 모델입니다.
    체류 중 작성하는 개인 일기를 테이블로 매핑합니다.

    Columns:
        diary_id: PK, UUID v7
        user_id: FK → users.user_id (작성자)
        room_stay_id: FK → room_stays.room_stay_id (체류)
        city_id: FK → cities.city_id (도시, 비정규화)
        guest_house_id: FK → guest_houses.guest_house_id (게스트하우스, 비정규화)
        title: 일기 제목 (max 50자)
        content: 일기 내용 (max 500자)
        mood: 감정 상태

    Indexes:
        - uq_diaries_room_stay_id_active: 체류당 1개의 활성 일기만 허용
          (partial unique index: WHERE deleted_at IS NULL)

    Mixins:
        AuditMixin: created_at, updated_at 자동 관리
        SoftDeleteMixin: deleted_at을 통한 soft delete 지원
    """

    __tablename__ = "diaries"

    diary_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.user_id"), nullable=False)
    room_stay_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("room_stays.room_stay_id"), nullable=False)
    city_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("cities.city_id"), nullable=False)
    guest_house_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("guest_houses.guest_house_id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mood: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (
        # 체류당 1개의 활성 일기만 허용하는 부분 유니크 인덱스
        Index(
            "uq_diaries_room_stay_id_active",
            "room_stay_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
