from bzero.domain.entities import Airship
from bzero.domain.errors import InvalidAirshipStatusError, NotFoundAirshipError
from bzero.domain.repositories.airship import AirshipRepository
from bzero.domain.value_objects import Id


class AirshipService:
    """비행선 도메인 서비스.

    비행선과 관련된 비즈니스 로직을 처리합니다.
    리포지토리를 통해 비행선 데이터에 접근하고, 도메인 규칙을 적용합니다.
    """

    def __init__(self, airship_repository: AirshipRepository):
        """서비스를 초기화합니다.

        Args:
            airship_repository: 비행선 리포지토리 인터페이스
        """
        self._airship_repository = airship_repository

    async def get_available_airships(self, offset: int = 0, limit: int = 100) -> tuple[list[Airship], int]:
        """이용 가능한(활성화된) 비행선 목록을 조회합니다.

        Args:
            offset: 조회 시작 위치 (기본값: 0)
            limit: 최대 조회 개수 (기본값: 100)

        Returns:
            (비행선 목록, 전체 개수) 튜플
        """
        airships = await self._airship_repository.find_all_by_active_state(is_active=True, limit=limit, offset=offset)
        total = await self._airship_repository.count_by(is_active=True)
        return airships, total

    async def get_airship_by_id(self, airship_id: Id) -> Airship:
        airship = await self._airship_repository.find_by_id(airship_id)
        if airship is None:
            raise NotFoundAirshipError
        return airship

    async def get_active_airship_by_id(self, airship_id: Id) -> Airship:
        airship = await self.get_airship_by_id(airship_id)
        if not airship.is_active:
            raise InvalidAirshipStatusError
        return airship
