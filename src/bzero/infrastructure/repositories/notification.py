from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from bzero.domain.entities.notification import Notification
from bzero.domain.repositories.notification import NotificationRepository, NotificationSyncRepository
from bzero.domain.value_objects import Id
from bzero.infrastructure.repositories.notification_core import NotificationRepositoryCore


class SqlAlchemyNotificationRepository(NotificationRepository):
    """SQLAlchemy 기반 Notification Repository (비동기).

    NotificationRepositoryCore를 위임하여 구현합니다.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, notification: Notification) -> Notification:
        return await self._session.run_sync(NotificationRepositoryCore.create, notification)

    async def find_by_user_id(self, user_id: Id, limit: int = 20) -> list[Notification]:
        # 하위 호환성 (find_all_by_user_id로 대체 가능하지만 인터페이스 유지)
        result, _ = await self._session.run_sync(
            NotificationRepositoryCore.find_all_by_user_id,
            user_id,
            0,
            limit,
        )
        return result

    async def find_all_by_user_id(self, user_id: Id, offset: int, limit: int) -> tuple[list[Notification], int]:
        return await self._session.run_sync(
            NotificationRepositoryCore.find_all_by_user_id,
            user_id,
            offset,
            limit,
        )

    async def count_unread_by_user_id(self, user_id: Id) -> int:
        return await self._session.run_sync(NotificationRepositoryCore.count_unread_by_user_id, user_id)

    async def find_by_id(self, notification_id: Id) -> Notification | None:
        return await self._session.run_sync(NotificationRepositoryCore.find_by_id, notification_id)

    async def update(self, notification: Notification) -> Notification:
        return await self._session.run_sync(NotificationRepositoryCore.update, notification)

    async def mark_all_as_read(self, user_id: Id) -> int:
        return await self._session.run_sync(NotificationRepositoryCore.mark_all_as_read, user_id)


class SqlAlchemyNotificationSyncRepository(NotificationSyncRepository):
    """SQLAlchemy 기반 Notification Repository (동기).

    Celery 등 동기 환경에서 사용합니다.
    """

    def __init__(self, session: Session):
        self._session = session

    def create(self, notification: Notification) -> Notification:
        return NotificationRepositoryCore.create(self._session, notification)
