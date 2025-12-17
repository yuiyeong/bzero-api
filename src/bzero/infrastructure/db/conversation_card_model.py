from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class ConversationCardModel(Base, AuditMixin, SoftDeleteMixin):
    """대화 카드 ORM 모델.

    룸 내 여행자들의 대화를 위한 주제 카드를 저장합니다.
    """

    __tablename__ = "conversation_cards"

    card_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    city_id: Mapped[UUID | None] = mapped_column(UUID, ForeignKey("cities.city_id"), nullable=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index(
            "idx_conversation_cards_city_active",
            "city_id",
            "is_active",
        ),
    )
