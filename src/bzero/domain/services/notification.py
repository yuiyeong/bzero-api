from zoneinfo import ZoneInfo

from bzero.domain.entities.notification import Notification
from bzero.domain.errors import ForbiddenError, NotFoundNotificationError
from bzero.domain.repositories.notification import NotificationRepository
from bzero.domain.value_objects import Id, NotificationType


class NotificationService:
    """알림 도메인 서비스.

    알림 생성, 조회, 읽음 처리 등의 도메인 로직을 담당합니다.
    """

    def __init__(self, notification_repository: NotificationRepository, timezone: ZoneInfo):
        self._notification_repository = notification_repository
        self._timezone = timezone

    async def create_notification(
        self,
        user_id: Id,
        notification_type: NotificationType,
        title: str,
        message: str,
    ) -> Notification:
        """알림을 생성합니다."""
        notification = Notification.create(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
        )
        return await self._notification_repository.create(notification)

    async def get_my_notifications(
        self,
        user_id: Id,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Notification], int]:
        """나의 알림 목록을 조회합니다."""
        return await self._notification_repository.find_all_by_user_id(user_id, offset, limit)

    async def get_unread_count(self, user_id: Id) -> int:
        """읽지 않은 알림 개수를 조회합니다."""
        return await self._notification_repository.count_unread_by_user_id(user_id)

    async def mark_as_read(self, notification_id: Id, user_id: Id) -> Notification:
        """알림을 읽음 처리합니다.

        Raises:
            NotFoundError: 알림이 존재하지 않을 때
            ForbiddenError: 본인의 알림이 아닐 때
        """
        notification = await self._notification_repository.find_by_id(notification_id)
        if not notification:
            raise NotFoundNotificationError

        if notification.user_id != user_id:
            raise ForbiddenError("본인의 알림만 읽음 처리할 수 있습니다.")

        if not notification.is_read:
            notification.mark_as_read()
            # updated_at 갱신 등은 Repository/DB 레벨에서 처리되거나 여기서 명시
            # 여기서는 도메인 엔티티 상태 변경 후 저장
            return await self._notification_repository.update(notification)

        return notification

    async def mark_all_as_read(self, user_id: Id) -> int:
        """나의 모든 알림을 읽음 처리합니다."""
        return await self._notification_repository.mark_all_as_read(user_id)
