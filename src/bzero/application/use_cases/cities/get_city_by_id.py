from bzero.application.results.city_result import CityResult
from bzero.domain.errors import NotFoundError
from bzero.domain.repositories.city import CityRepository
from bzero.domain.value_objects import Id


class GetCityByIdUseCase:
    """
    도시 ID로 도시 상세 정보 조회 UseCase
    """

    def __init__(self, city_repository: CityRepository):
        self._city_repository = city_repository

    async def execute(self, city_id: str) -> CityResult:
        """
        Args:
            city_id: 조회할 도시 ID (UUID hex 문자열)

        Returns:
            CityResult

        Raises:
            NotFoundError: 도시가 존재하지 않을 때
            BadRequestError: 잘못된 UUID 형식일 때
        """
        from bzero.domain.errors import BadRequestError, ErrorCode

        try:
            city_id_obj = Id.from_hex(city_id)
        except (ValueError, AttributeError):
            raise BadRequestError(ErrorCode.INVALID_PARAMETER)

        city = await self._city_repository.find_by_id(city_id_obj)
        if city is None:
            raise NotFoundError(ErrorCode.NOT_FOUND)

        return CityResult.create_from(city)
