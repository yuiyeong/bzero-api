from sqlalchemy import Boolean, Date, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class DiaryModel(Base, AuditMixin, SoftDeleteMixin):
    """일기 ORM 모델"""

    __tablename__ = "diaries"

    diary_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.user_id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mood: Mapped[str] = mapped_column(String(10), nullable=False)
    diary_date: Mapped[Date] = mapped_column(Date, nullable=False)
    city_id: Mapped[UUID | None] = mapped_column(UUID, ForeignKey("cities.city_id"), nullable=True)
    has_earned_points: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "diary_date", name="uq_diaries_user_id_diary_date"),
        Index("idx_diaries_user_id_diary_date", "user_id", "diary_date"),
        Index("idx_diaries_user_id", "user_id"),
    )
