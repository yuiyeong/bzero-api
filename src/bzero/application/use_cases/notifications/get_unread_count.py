from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.services.notification import NotificationService
from bzero.domain.value_objects import AuthProvider


class GetUnreadNotificationCountUseCase:
    """읽지 않은 알림 개수 조회 유스케이스."""

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
        """읽지 않은 알림 개수를 조회합니다."""
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        return await self._notification_service.get_unread_count(user.user_id)
