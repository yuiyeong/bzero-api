from abc import ABC, abstractmethod

from bzero.domain.entities.city import City
from bzero.domain.value_objects import Id


class CityRepository(ABC):
    """도시 리포지토리 인터페이스"""

    @abstractmethod
    async def find_by_id(self, city_id: Id) -> City | None:
        """도시 ID로 도시를 조회합니다.

        Args:
            city_id: 조회할 도시의 ID

        Returns:
            도시 엔티티. 없으면 None을 반환합니다.
        """

    @abstractmethod
    async def find_active_cities(self) -> list[City]:
        """활성화된 도시 목록을 조회합니다.

        display_order 순서대로 정렬하여 반환합니다.

        Returns:
            활성화된 도시 목록 (display_order 오름차순)
        """

    @abstractmethod
    async def find_cities_by_phase(self, phase: int) -> list[City]:
        """Phase별 도시 목록을 조회합니다.

        Args:
            phase: 조회할 Phase (1=MVP, 2=확장)

        Returns:
            해당 Phase의 도시 목록 (display_order 오름차순)
        """
