from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class ChatMessageModel(Base, AuditMixin, SoftDeleteMixin):
    """채팅 메시지 ORM 모델.

    룸 내 사용자들 간의 대화 메시지를 저장합니다.
    """

    __tablename__ = "chat_messages"

    message_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    room_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("rooms.room_id"), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(UUID, ForeignKey("users.user_id"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    card_id: Mapped[UUID | None] = mapped_column(
        UUID, ForeignKey("conversation_cards.card_id"), nullable=True
    )
    message_type: Mapped[str] = mapped_column(String(20), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index(
            "idx_chat_messages_room_created",
            "room_id",
            "created_at",
        ),
        Index(
            "idx_chat_messages_expires",
            "expires_at",
        ),
    )
