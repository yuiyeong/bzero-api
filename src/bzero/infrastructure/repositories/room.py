from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.room import Room
from bzero.domain.repositories.room import RoomRepository, RoomSyncRepository
from bzero.domain.value_objects import Id
from bzero.infrastructure.repositories.room_core import RoomRepositoryCore


class SqlAlchemyRoomRepository(RoomRepository):
    """SQLAlchemy 기반 RoomRepository (비동기).

    RoomRepositoryCore의 동기 메서드를 run_sync로 호출합니다.
    이 패턴을 통해 로직 중복 없이 비동기 인터페이스를 제공합니다.

    Attributes:
        _session: SQLAlchemy AsyncSession 인스턴스
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, room: Room) -> Room:
        return await self._session.run_sync(RoomRepositoryCore.create, room)

    async def find_by_room_id(self, room_id: Id) -> Room | None:
        return await self._session.run_sync(RoomRepositoryCore.find_by_room_id, room_id)

    async def find_available_by_guest_house_id_for_update(self, guest_house_id: Id) -> list[Room]:
        return await self._session.run_sync(
            RoomRepositoryCore.find_available_by_guest_house_id_for_update, guest_house_id
        )

    async def update(self, room: Room) -> Room:
        return await self._session.run_sync(RoomRepositoryCore.update, room)


class SqlAlchemyRoomSyncRepository(RoomSyncRepository):
    """SQLAlchemy 기반 RoomRepository (동기).

    RoomRepositoryCore의 동기 메서드를 직접 호출합니다.
    주로 Celery 백그라운드 태스크에서 사용됩니다.

    Attributes:
        _session: SQLAlchemy Session 인스턴스
    """

    def __init__(self, session):
        self._session = session

    def create(self, room: Room) -> Room:
        return RoomRepositoryCore.create(self._session, room)

    def find_by_room_id(self, room_id: Id) -> Room | None:
        return RoomRepositoryCore.find_by_room_id(self._session, room_id)

    def find_available_by_guest_house_id_for_update(self, guest_house_id: Id) -> list[Room]:
        return RoomRepositoryCore.find_available_by_guest_house_id_for_update(self._session, guest_house_id)

    def update(self, room: Room) -> Room:
        return RoomRepositoryCore.update(self._session, room)
