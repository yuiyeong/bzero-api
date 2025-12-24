from sqlalchemy import Boolean, ForeignKey, Index, Integer, Text, text
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class CityQuestionModel(Base, AuditMixin, SoftDeleteMixin):
    """CityQuestion SQLAlchemy 모델.

    CityQuestion 도메인 엔티티의 영속성을 담당하는 ORM 모델입니다.
    각 도시에 속한 사전 정의된 질문을 테이블로 매핑합니다.

    Columns:
        city_question_id: PK, UUID v7
        city_id: FK → cities.city_id (도시)
        question: 질문 내용
        display_order: 표시 순서
        is_active: 활성화 여부

    Indexes:
        - uq_city_questions_city_id_display_order_active: 도시별 display_order 유니크
          (partial unique index: WHERE deleted_at IS NULL)

    Mixins:
        AuditMixin: created_at, updated_at 자동 관리
        SoftDeleteMixin: deleted_at을 통한 soft delete 지원
    """

    __tablename__ = "city_questions"

    city_question_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    city_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("cities.city_id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        # 도시별 display_order 유니크 (활성 질문에 대해서만)
        Index(
            "uq_city_questions_city_id_display_order_active",
            "city_id",
            "display_order",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
