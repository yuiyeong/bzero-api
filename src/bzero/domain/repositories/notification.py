from abc import ABC, abstractmethod

from bzero.domain.entities.notification import Notification
from bzero.domain.value_objects import Id


class NotificationRepository(ABC):
    """알림 리포지토리 인터페이스."""

    @abstractmethod
    async def create(self, notification: Notification) -> Notification:
        """알림을 생성합니다.

        Args:
            notification: 생성할 알림 엔티티

        Returns:
            생성된 알림 엔티티
        """

    @abstractmethod
    async def find_by_user_id(self, user_id: Id, limit: int = 20) -> list[Notification]:
        """사용자의 알림 목록을 최신순으로 조회합니다.

        Args:
            user_id: 사용자 ID
            limit: 조회할 최대 개수 (기본값 20)

        Returns:
            알림 목록
        """


class NotificationSyncRepository(ABC):
    """알림 리포지토리 인터페이스 (동기)."""

    @abstractmethod
    def create(self, notification: Notification) -> Notification:
        """알림을 생성합니다.

        Args:
            notification: 생성할 알림 엔티티

        Returns:
            생성된 알림 엔티티
        """
