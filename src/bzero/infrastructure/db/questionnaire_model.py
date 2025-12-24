from sqlalchemy import ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class QuestionnaireModel(Base, AuditMixin, SoftDeleteMixin):
    """Questionnaire SQLAlchemy 모델.

    Questionnaire 도메인 엔티티의 영속성을 담당하는 ORM 모델입니다.
    체류 중 도시 질문에 대한 답변(1문 1답)을 테이블로 매핑합니다.

    Columns:
        questionnaire_id: PK, UUID v7
        user_id: FK → users.user_id (작성자)
        room_stay_id: FK → room_stays.room_stay_id (체류)
        city_question_id: FK → city_questions.city_question_id (질문)
        city_question: 도시 질문 내용(스냅샷)
        answer: 답변 내용 (max 200자)
        city_id: FK → cities.city_id (도시, 비정규화)
        guest_house_id: FK → guest_houses.guest_house_id (게스트하우스, 비정규화)

    Indexes:
        - uq_questionnaires_room_stay_question_active: 체류당 질문당 1개의 활성 답변만 허용
          (partial unique index: WHERE deleted_at IS NULL)

    Mixins:
        AuditMixin: created_at, updated_at 자동 관리
        SoftDeleteMixin: deleted_at을 통한 soft delete 지원
    """

    __tablename__ = "questionnaires"

    questionnaire_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.user_id"), nullable=False)
    room_stay_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("room_stays.room_stay_id"), nullable=False)
    city_question_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("city_questions.city_question_id"), nullable=False)
    city_question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    city_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("cities.city_id"), nullable=False)
    guest_house_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("guest_houses.guest_house_id"), nullable=False)

    __table_args__ = (
        # 체류당 질문당 1개의 활성 답변만 허용하는 부분 유니크 인덱스
        Index(
            "uq_questionnaires_room_stay_question_active",
            "room_stay_id",
            "city_question_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
