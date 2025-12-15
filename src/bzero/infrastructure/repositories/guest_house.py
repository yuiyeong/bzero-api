from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from bzero.domain.entities.guest_house import GuestHouse
from bzero.domain.repositories.guest_house import (
    GuestHouseRepository,
    GuestHouseSyncRepository,
)
from bzero.domain.value_objects import Id
from bzero.infrastructure.repositories.guest_house_core import GuestHouseRepositoryCore


class SqlAlchemyGuestHouseRepository(GuestHouseRepository):
    """SQLAlchemy 기반 GuestHouseRepository (비동기).

    GuestHouseRepositoryCore의 동기 메서드를 run_sync로 호출합니다.
    이 패턴을 통해 로직 중복 없이 비동기 인터페이스를 제공합니다.

    Attributes:
        _session: SQLAlchemy AsyncSession 인스턴스
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, guesthouse: GuestHouse) -> GuestHouse:
        return await self._session.run_sync(GuestHouseRepositoryCore.create, guesthouse)

    async def find_by_guesthouse_id(self, guesthouse_id: Id) -> GuestHouse | None:
        return await self._session.run_sync(GuestHouseRepositoryCore.find_by_guesthouse_id, guesthouse_id)

    async def find_all_by_city_id(self, city_id: Id) -> list[GuestHouse]:
        return await self._session.run_sync(GuestHouseRepositoryCore.find_all_by_city_id, city_id)

    async def find_available_one_by_city_id(self, city_id: Id) -> GuestHouse | None:
        return await self._session.run_sync(GuestHouseRepositoryCore.find_available_one_by_city_id, city_id)


class SqlAlchemyGuestHouseSyncRepository(GuestHouseSyncRepository):
    """SQLAlchemy 기반 GuestHouseRepository (동기).

    GuestHouseRepositoryCore의 동기 메서드를 직접 호출합니다.
    주로 Celery 백그라운드 태스크에서 사용됩니다.

    Attributes:
        _session: SQLAlchemy Session 인스턴스
    """

    def __init__(self, session: Session):
        self._session = session

    def create(self, guesthouse: GuestHouse) -> GuestHouse:
        return GuestHouseRepositoryCore.create(self._session, guesthouse)

    def find_by_guesthouse_id(self, guesthouse_id: Id) -> GuestHouse | None:
        return GuestHouseRepositoryCore.find_by_guesthouse_id(self._session, guesthouse_id)

    def find_all_by_city_id(self, city_id: Id) -> list[GuestHouse]:
        return GuestHouseRepositoryCore.find_all_by_city_id(self._session, city_id)

    def find_available_one_by_city_id(self, city_id: Id) -> GuestHouse | None:
        return GuestHouseRepositoryCore.find_available_one_by_city_id(self._session, city_id)
