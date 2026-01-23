from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.notification import Notification
from bzero.domain.services.notification import NotificationService
from bzero.domain.value_objects import AuthProvider


class GetNotificationsUseCase:
    """알림 목록 조회 유스케이스."""

    def __init__(
        self,
        session: AsyncSession,
        notification_service: NotificationService,
        user_service,  # Type hint User Service if needed, or pass IDs directly
    ):
        self._session = session
        self._notification_service = notification_service
        self._user_service = user_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Notification], int]:
        """나의 알림 목록을 조회합니다."""
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        return await self._notification_service.get_my_notifications(
            user_id=user.user_id,
            offset=offset,
            limit=limit,
        )
