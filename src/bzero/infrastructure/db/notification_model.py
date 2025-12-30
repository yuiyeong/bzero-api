from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base


class NotificationModel(Base, AuditMixin):
    """Notification SQLAlchemy 모델.

    사용자에게 발송된 알림 내역을 저장합니다.

    Columns:
        notification_id: PK, UUID v7
        user_id: FK -> users.user_id
        type: 알림 유형 (CHECKOUT_REMINDER 등)
        title: 알림 제목
        message: 알림 내용
        is_read: 읽음 여부
    """

    __tablename__ = "notifications"

    notification_id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
