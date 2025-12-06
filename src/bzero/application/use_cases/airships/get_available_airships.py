from bzero.application.results import PaginatedResult
from bzero.application.results.airship_result import AirshipResult
from bzero.domain.services import AirshipService


class GetAvailableAirshipsUseCase:
    """이용 가능한 비행선 목록 조회 유스케이스.

    활성화된 비행선 목록을 페이지네이션과 함께 조회합니다.
    B0 터미널에서 사용자가 선택할 수 있는 비행선 옵션을 제공합니다.
    """

    def __init__(self, airship_service: AirshipService):
        """유스케이스를 초기화합니다.

        Args:
            airship_service: 비행선 도메인 서비스
        """
        self._airship_service = airship_service

    async def execute(self, offset: int, limit: int) -> PaginatedResult[AirshipResult]:
        """유스케이스를 실행합니다.

        Args:
            offset: 조회 시작 위치
            limit: 최대 조회 개수

        Returns:
            페이지네이션된 비행선 결과 목록
        """
        available_airships, total = await self._airship_service.get_available_airships(offset=offset, limit=limit)
        items = [AirshipResult.create_from(airship) for airship in available_airships]
        return PaginatedResult(items=items, total=total, offset=offset, limit=limit)
