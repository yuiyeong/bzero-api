from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from bzero.domain.entities.notification import Notification
from bzero.domain.repositories.notification import NotificationRepository, NotificationSyncRepository
from bzero.domain.value_objects import Id, NotificationType
from bzero.infrastructure.db.notification_model import NotificationModel


class SqlAlchemyNotificationRepository(NotificationRepository):
    """SQLAlchemy 기반 Notification Repository."""

    def __init__(self, session: AsyncSession):
        """리포지토리를 초기화합니다.

        Args:
            session: SQLAlchemy AsyncSession 인스턴스
        """
        self._session = session

    async def create(self, notification: Notification) -> Notification:
        """알림을 생성합니다."""
        model = self._to_model(notification)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def find_by_user_id(self, user_id: Id, limit: int = 20) -> list[Notification]:
        """사용자의 알림 목록을 최신순으로 조회합니다."""
        stmt = (
            select(NotificationModel)
            .where(NotificationModel.user_id == user_id.value)
            .order_by(NotificationModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    def _to_model(self, entity: Notification) -> NotificationModel:
        return NotificationModel(
            notification_id=entity.notification_id.value,
            user_id=entity.user_id.value,
            type=entity.type.value,
            title=entity.title,
            message=entity.message,
            is_read=entity.is_read,
            created_at=entity.created_at,
        )

    def _to_entity(self, model: NotificationModel) -> Notification:
        return Notification(
            notification_id=Id(model.notification_id),
            user_id=Id(model.user_id),
            type=NotificationType(model.type),
            title=model.title,
            message=model.message,
            is_read=model.is_read,
            created_at=model.created_at,
        )


class SqlAlchemyNotificationSyncRepository(NotificationSyncRepository):
    """SQLAlchemy 기반 Notification Repository (동기)."""

    def __init__(self, session: Session):
        self._session = session

    def create(self, notification: Notification) -> Notification:
        """알림을 생성합니다."""
        model = self._to_model(notification)
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_entity(model)

    def _to_model(self, entity: Notification) -> NotificationModel:
        return NotificationModel(
            notification_id=entity.notification_id.value,
            user_id=entity.user_id.value,
            type=entity.type.value,
            title=entity.title,
            message=entity.message,
            is_read=entity.is_read,
            created_at=entity.created_at,
        )

    def _to_entity(self, model: NotificationModel) -> Notification:
        return Notification(
            notification_id=Id(model.notification_id),
            user_id=Id(model.user_id),
            type=NotificationType(model.type),
            title=model.title,
            message=model.message,
            is_read=model.is_read,
            created_at=model.created_at,
        )
