"""DirectMessageRoom Repository 구현체 (비동기).

SqlAlchemy를 사용한 1:1 대화방 리포지토리 구현입니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.direct_message_room import DirectMessageRoom
from bzero.domain.repositories.direct_message_room import DirectMessageRoomRepository
from bzero.domain.value_objects import DMStatus, Id
from bzero.infrastructure.repositories.direct_message_room_core import (
    DirectMessageRoomRepositoryCore,
)


class SqlAlchemyDirectMessageRoomRepository(DirectMessageRoomRepository):
    """SqlAlchemy 기반 DirectMessageRoom 리포지토리 (비동기).

    AsyncSession을 사용하여 비동기 DB 작업을 수행합니다.
    Core 메서드를 run_sync로 호출합니다.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, dm_room: DirectMessageRoom) -> DirectMessageRoom:
        """대화방을 생성합니다."""
        return await self._session.run_sync(DirectMessageRoomRepositoryCore.create, dm_room)

    async def find_by_id(self, dm_room_id: Id) -> DirectMessageRoom | None:
        """ID로 대화방을 조회합니다."""
        return await self._session.run_sync(DirectMessageRoomRepositoryCore.find_by_id, dm_room_id)

    async def find_by_room_and_users(
        self,
        room_id: Id,
        user1_id: Id,
        user2_id: Id,
    ) -> DirectMessageRoom | None:
        """룸과 사용자로 대화방을 조회합니다."""
        return await self._session.run_sync(
            DirectMessageRoomRepositoryCore.find_by_room_and_users,
            room_id,
            user1_id,
            user2_id,
        )

    async def find_by_user_and_statuses(
        self,
        user_id: Id,
        statuses: list[DMStatus],
        limit: int = 50,
        offset: int = 0,
    ) -> list[DirectMessageRoom]:
        """사용자와 상태로 대화방 목록을 조회합니다."""
        return await self._session.run_sync(
            DirectMessageRoomRepositoryCore.find_by_user_and_statuses,
            user_id,
            statuses,
            limit,
            offset,
        )

    async def update(self, dm_room: DirectMessageRoom) -> DirectMessageRoom:
        """대화방 정보를 업데이트합니다."""
        return await self._session.run_sync(DirectMessageRoomRepositoryCore.update, dm_room)

    async def soft_delete_by_room_id(self, room_id: Id) -> int:
        """룸 ID로 대화방들을 soft delete 처리합니다."""
        return await self._session.run_sync(
            DirectMessageRoomRepositoryCore.soft_delete_by_room_id, room_id
        )

    async def count_by_user_and_statuses(
        self,
        user_id: Id,
        statuses: list[DMStatus],
    ) -> int:
        """사용자와 상태별 대화방 개수를 조회합니다."""
        return await self._session.run_sync(
            DirectMessageRoomRepositoryCore.count_by_user_and_statuses,
            user_id,
            statuses,
        )
