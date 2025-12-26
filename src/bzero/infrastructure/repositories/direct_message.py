"""DirectMessage Repository 구현체 (비동기).

SqlAlchemy를 사용한 1:1 메시지 리포지토리 구현입니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.direct_message import DirectMessage
from bzero.domain.repositories.direct_message import DirectMessageRepository
from bzero.domain.value_objects import Id
from bzero.infrastructure.repositories.direct_message_core import DirectMessageRepositoryCore


class SqlAlchemyDirectMessageRepository(DirectMessageRepository):
    """SqlAlchemy 기반 DirectMessage 리포지토리 (비동기).

    AsyncSession을 사용하여 비동기 DB 작업을 수행합니다.
    Core 메서드를 run_sync로 호출합니다.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, message: DirectMessage) -> DirectMessage:
        """메시지를 생성합니다."""
        return await self._session.run_sync(DirectMessageRepositoryCore.create, message)

    async def find_by_id(self, dm_id: Id) -> DirectMessage | None:
        """ID로 메시지를 조회합니다."""
        return await self._session.run_sync(DirectMessageRepositoryCore.find_by_id, dm_id)

    async def find_by_dm_room_paginated(
        self,
        dm_room_id: Id,
        cursor: Id | None = None,
        limit: int = 50,
    ) -> list[DirectMessage]:
        """대화방별 메시지를 cursor 기반 페이지네이션으로 조회합니다."""
        return await self._session.run_sync(
            DirectMessageRepositoryCore.find_by_dm_room_paginated,
            dm_room_id,
            cursor,
            limit,
        )

    async def mark_as_read_by_dm_room_and_user(
        self,
        dm_room_id: Id,
        user_id: Id,
    ) -> int:
        """대화방의 사용자가 수신한 메시지를 읽음 처리합니다."""
        return await self._session.run_sync(
            DirectMessageRepositoryCore.mark_as_read_by_dm_room_and_user,
            dm_room_id,
            user_id,
        )

    async def count_unread_by_dm_room_and_user(
        self,
        dm_room_id: Id,
        user_id: Id,
    ) -> int:
        """읽지 않은 메시지 개수를 조회합니다."""
        return await self._session.run_sync(
            DirectMessageRepositoryCore.count_unread_by_dm_room_and_user,
            dm_room_id,
            user_id,
        )

    async def find_latest_by_dm_room(self, dm_room_id: Id) -> DirectMessage | None:
        """대화방의 가장 최근 메시지를 조회합니다."""
        return await self._session.run_sync(
            DirectMessageRepositoryCore.find_latest_by_dm_room, dm_room_id
        )
