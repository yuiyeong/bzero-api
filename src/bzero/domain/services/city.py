from bzero.domain.entities.city import City
from bzero.domain.errors import CityNotFoundError
from bzero.domain.repositories.city import CityRepository
from bzero.domain.value_objects import Id


class CityService:
    """도시 도메인 서비스

    City 조회를 담당합니다.
    주의: 모든 메서드는 데이터베이스 트랜잭션 내에서 호출되어야 합니다.
    """

    def __init__(self, city_repository: CityRepository):
        self._city_repository = city_repository

    async def get_active_cities(
        self, offset: int = 0, limit: int = 20
    ) -> tuple[list[City], int]:
        """활성화된 도시 목록을 조회합니다.

        display_order 순서대로 정렬하여 반환합니다.

        Args:
            offset: 조회 시작 위치 (기본값: 0)
            limit: 조회할 최대 개수 (기본값: 20)

        Returns:
            (활성화된 도시 목록, 전체 개수) 튜플
        """
        cities = await self._city_repository.find_active_cities(offset, limit)
        total = await self._city_repository.count_active_cities()
        return cities, total

    async def get_city_by_id(self, city_id: Id) -> City:
        """도시 ID로 도시를 조회합니다.

        Args:
            city_id: 조회할 도시의 ID

        Returns:
            조회된 City 엔티티

        Raises:
            CityNotFoundError: 도시가 존재하지 않을 때
        """
        city = await self._city_repository.find_by_id(city_id)
        if city is None:
            raise CityNotFoundError()

        return city
