from dataclasses import dataclass
from datetime import datetime

from bzero.domain.value_objects import Id, NotificationType


@dataclass
class Notification:
    """알림 엔티티.

    사용자에게 발송된 시스템 알림을 나타냅니다.

    Attributes:
        notification_id: 알림 고유 식별자 (UUID v7)
        user_id: 수신자 ID (FK)
        type: 알림 유형 (CHECKOUT_REMINDER 등)
        title: 알림 제목
        message: 알림 본문
        is_read: 읽음 여부
        created_at: 생성 시각
    """

    notification_id: Id
    user_id: Id
    type: NotificationType
    title: str
    message: str
    is_read: bool
    created_at: datetime

    @classmethod
    def create(
        cls,
        user_id: Id,
        notification_type: NotificationType,
        title: str,
        message: str,
    ) -> "Notification":
        """새 알림을 생성합니다.

        Args:
            user_id: 수신자 ID
            notification_type: 알림 유형
            title: 제목
            message: 본문

        Returns:
            생성된 알림 엔티티 (ID 자동 생성, 안 읽음 상태)
        """
        now = datetime.now()
        return cls(
            notification_id=Id(),
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            is_read=False,
            created_at=now,
        )

    def mark_as_read(self) -> None:
        """알림을 읽음 처리합니다."""
        self.is_read = True
