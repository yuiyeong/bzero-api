from bzero.application.results.city_result import CityResult
from bzero.domain.errors import BadRequestError, ErrorCode
from bzero.domain.services.city import CityService
from bzero.domain.value_objects import Id


class GetCityByIdUseCase:
    """
    도시 ID로 도시 상세 정보 조회 UseCase
    """

    def __init__(self, city_service: CityService):
        self._city_service = city_service

    async def execute(self, city_id: str) -> CityResult:
        """
        Args:
            city_id: 조회할 도시 ID (UUID hex 문자열)

        Returns:
            CityResult

        Raises:
            CityNotFoundError: 도시가 존재하지 않을 때
            BadRequestError: 잘못된 UUID 형식일 때
        """
        try:
            city_id_obj = Id.from_hex(city_id)
        except (ValueError, AttributeError):
            raise BadRequestError(ErrorCode.INVALID_PARAMETER)

        city = await self._city_service.get_city_by_id(city_id_obj)
        return CityResult.create_from(city)
