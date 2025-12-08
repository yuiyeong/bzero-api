from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class QuestionnaireModel(Base, AuditMixin, SoftDeleteMixin):
    """문답지 ORM 모델"""

    __tablename__ = "questionnaires"

    questionnaire_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.user_id"), nullable=False, index=True)
    city_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("cities.city_id"), nullable=False, index=True)
    question_1_answer: Mapped[str] = mapped_column(String(200), nullable=False)
    question_2_answer: Mapped[str] = mapped_column(String(200), nullable=False)
    question_3_answer: Mapped[str] = mapped_column(String(200), nullable=False)
    has_earned_points: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
