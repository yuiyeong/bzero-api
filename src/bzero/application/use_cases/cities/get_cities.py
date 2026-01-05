from bzero.application.results.city_result import CityResult
from bzero.application.results.common import PaginatedResult
from bzero.domain.services.city import CityService


class GetCitiesUseCase:
    """
    도시 목록 조회 UseCase

    display_order 순서대로 정렬된 도시 목록을 조회합니다.
    """

    def __init__(self, city_service: CityService):
        self._city_service = city_service

    async def execute(self, offset: int = 0, limit: int = 20, active_only: bool = True) -> PaginatedResult[CityResult]:
        """
        Args:
            offset: 조회 시작 위치 (기본값: 0)
            limit: 조회할 최대 개수 (기본값: 20)
            active_only: 활성화된 도시만 조회할지 여부 (기본값: True)

        Returns:
            도시 목록 및 pagination 정보
        """
        cities, total = await self._city_service.get_cities(offset, limit, active_only)
        city_results = [CityResult.create_from(city) for city in cities]
        return PaginatedResult(items=city_results, total=total, offset=offset, limit=limit)
