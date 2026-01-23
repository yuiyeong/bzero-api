from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from bzero.domain.entities.notification import Notification
from bzero.domain.value_objects import NotificationType


class NotificationResponse(BaseModel):
    """알림 응답 스키마."""

    model_config = ConfigDict(from_attributes=True)

    notification_id: str = Field(..., description="알림 ID")
    type: NotificationType = Field(..., description="알림 유형")
    title: str = Field(..., description="제목")
    message: str = Field(..., description="메시지")
    is_read: bool = Field(..., description="읽음 여부")
    created_at: datetime = Field(..., description="생성 일시")

    @classmethod
    def create_from(cls, notification: Notification) -> "NotificationResponse":
        return cls(
            notification_id=notification.notification_id.value.hex,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            is_read=notification.is_read,
            created_at=notification.created_at,
        )


class UnreadCountResponse(BaseModel):
    """읽지 않은 알림 개수 응답 스키마."""

    count: int = Field(..., description="읽지 않은 알림 개수")
