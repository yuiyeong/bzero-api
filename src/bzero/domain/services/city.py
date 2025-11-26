from bzero.domain.entities.city import City
from bzero.domain.errors import NotFoundError
from bzero.domain.repositories.city import CityRepository
from bzero.domain.value_objects import Id


class CityService:
    """도시 도메인 서비스

    City 조회를 담당합니다.
    주의: 모든 메서드는 데이터베이스 트랜잭션 내에서 호출되어야 합니다.
    """

    def __init__(self, city_repository: CityRepository):
        self._city_repository = city_repository

    async def get_active_cities(self) -> list[City]:
        """활성화된 도시 목록을 조회합니다.

        display_order 순서대로 정렬하여 반환합니다.

        Returns:
            활성화된 도시 목록 (display_order 오름차순)
        """
        return await self._city_repository.find_active_cities()

    async def get_city_by_id(self, city_id: Id) -> City:
        """도시 ID로 도시를 조회합니다.

        Args:
            city_id: 조회할 도시의 ID

        Returns:
            조회된 City 엔티티

        Raises:
            NotFoundError: 도시가 존재하지 않을 때
        """
        from bzero.domain.errors import ErrorCode

        city = await self._city_repository.find_by_id(city_id)
        if city is None:
            raise NotFoundError(ErrorCode.NOT_FOUND)

        return city
