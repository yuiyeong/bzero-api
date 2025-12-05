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
    async def find_active_cities(self, offset: int = 0, limit: int = 20) -> list[City]:
        """활성화된 도시 목록을 조회합니다.

        display_order 순서대로 정렬하여 반환합니다.

        Args:
            offset: 조회 시작 위치 (기본값: 0)
            limit: 조회할 최대 개수 (기본값: 20)

        Returns:
            활성화된 도시 목록 (display_order 오름차순)
        """

    @abstractmethod
    async def count_active_cities(self) -> int:
        """활성화된 도시의 총 개수를 조회합니다.

        Returns:
            활성화된 도시의 총 개수
        """
