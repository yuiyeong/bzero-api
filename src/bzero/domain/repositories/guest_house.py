from abc import ABC, abstractmethod

from bzero.domain.entities.guest_house import GuestHouse
from bzero.domain.value_objects import Id


class GuestHouseRepository(ABC):
    """게스트하우스 리포지토리 인터페이스 (비동기)."""

    @abstractmethod
    async def create(self, guesthouse: GuestHouse) -> GuestHouse:
        """게스트하우스를 생성합니다.

        Args:
            guesthouse: 생성할 게스트하우스 엔티티

        Returns:
            생성된 게스트하우스 엔티티
        """

    @abstractmethod
    async def find_by_guesthouse_id(self, guesthouse_id: Id) -> GuestHouse | None:
        """게스트하우스 ID로 조회합니다.

        Args:
            guesthouse_id: 게스트하우스 ID

        Returns:
            게스트하우스 엔티티 또는 None
        """

    @abstractmethod
    async def find_all_by_city_id(self, city_id: Id) -> list[GuestHouse]:
        """도시 ID로 모든 게스트하우스를 조회합니다.

        Args:
            city_id: 도시 ID

        Returns:
            해당 도시의 게스트하우스 목록
        """

    @abstractmethod
    async def find_available_one_by_city_id(self, city_id: Id) -> GuestHouse | None:
        """도시에서 이용 가능한 게스트하우스 하나를 조회합니다.

        활성화된(is_active=True) 게스트하우스 중 하나를 반환합니다.

        Args:
            city_id: 도시 ID

        Returns:
            이용 가능한 게스트하우스 엔티티 또는 None
        """


class GuestHouseSyncRepository(ABC):
    """게스트하우스 리포지토리 인터페이스 (동기).

    Celery 백그라운드 태스크에서 사용됩니다.
    """

    @abstractmethod
    def create(self, guesthouse: GuestHouse) -> GuestHouse:
        """게스트하우스를 생성합니다.

        Args:
            guesthouse: 생성할 게스트하우스 엔티티

        Returns:
            생성된 게스트하우스 엔티티
        """

    @abstractmethod
    def find_by_guesthouse_id(self, guesthouse_id: Id) -> GuestHouse | None:
        """게스트하우스 ID로 조회합니다.

        Args:
            guesthouse_id: 게스트하우스 ID

        Returns:
            게스트하우스 엔티티 또는 None
        """

    @abstractmethod
    def find_all_by_city_id(self, city_id: Id) -> list[GuestHouse]:
        """도시 ID로 모든 게스트하우스를 조회합니다.

        Args:
            city_id: 도시 ID

        Returns:
            해당 도시의 게스트하우스 목록
        """

    @abstractmethod
    def find_available_one_by_city_id(self, city_id: Id) -> GuestHouse | None:
        """도시에서 이용 가능한 게스트하우스 하나를 조회합니다.

        활성화된(is_active=True) 게스트하우스 중 하나를 반환합니다.

        Args:
            city_id: 도시 ID

        Returns:
            이용 가능한 게스트하우스 엔티티 또는 None
        """
