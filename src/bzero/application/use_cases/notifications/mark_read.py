from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.notification import Notification
from bzero.domain.services.notification import NotificationService
from bzero.domain.value_objects import AuthProvider, Id


class MarkNotificationAsReadUseCase:
    """알림 읽음 처리 유스케이스."""

    def __init__(
        self,
        session: AsyncSession,
        notification_service: NotificationService,
        user_service,
    ):
        self._session = session
        self._notification_service = notification_service
        self._user_service = user_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
        notification_id: str,
    ) -> Notification:
        """특정 알림을 읽음 처리합니다."""
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        notification = await self._notification_service.mark_as_read(
            notification_id=Id.from_hex(notification_id),
            user_id=user.user_id,
        )
        await self._session.commit()
        return notification


class MarkAllNotificationsAsReadUseCase:
    """전체 알림 읽음 처리 유스케이스."""

    def __init__(
        self,
        session: AsyncSession,
        notification_service: NotificationService,
        user_service,
    ):
        self._session = session
        self._notification_service = notification_service
        self._user_service = user_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
    ) -> int:
        """나의 모든 알림을 읽음 처리합니다."""
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        count = await self._notification_service.mark_all_as_read(user.user_id)
        await self._session.commit()
        return count
