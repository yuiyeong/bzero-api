from bzero.application.results.city_result import CityResult
from bzero.domain.repositories.city import CityRepository


class GetActiveCitiesUseCase:
    """
    활성화된 도시 목록 조회 UseCase

    display_order 순서대로 정렬된 활성화된 도시 목록을 조회합니다.
    """

    def __init__(self, city_repository: CityRepository):
        self._city_repository = city_repository

    async def execute(self) -> list[CityResult]:
        """
        Returns:
            활성화된 도시 목록 (display_order 오름차순)
        """
        cities = await self._city_repository.find_active_cities()
        return [CityResult.create_from(city) for city in cities]
