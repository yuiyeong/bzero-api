from typing import Annotated

from fastapi import APIRouter, Query

from bzero.application.use_cases.airships import GetAvailableAirshipsUseCase
from bzero.presentation.api.dependencies import CurrentAirshipService
from bzero.presentation.schemas.airship import AirshipResponse
from bzero.presentation.schemas.common import ListResponse, Pagination


router = APIRouter(prefix="/airships", tags=["airships"])


@router.get(
    "",
    response_model=ListResponse[AirshipResponse],
    summary="이용 가능한 비행선 목록 조회",
    description="현재 이용 가능한 비행선 목록을 페이지네이션하여 조회합니다.",
)
async def get_available_airships(
    airship_service: CurrentAirshipService,
    offset: Annotated[int, Query(ge=0, description="조회 시작 위치")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="조회할 최대 개수")] = 20,
) -> ListResponse[AirshipResponse]:
    """이용 가능한 비행선 목록을 조회합니다.

    Args:
        airship_service: 비행선 도메인 서비스
        offset: 조회 시작 위치 (기본값: 0)
        limit: 조회할 최대 개수 (기본값: 20, 최대: 100)

    Returns:
        ListResponse[AirshipResponse]: 비행선 목록과 페이지네이션 정보
    """
    result = await GetAvailableAirshipsUseCase(airship_service).execute(offset, limit)
    return ListResponse(
        list=[AirshipResponse.create_from(airship) for airship in result.items],
        pagination=Pagination(total=result.total, offset=result.offset, limit=result.limit),
    )
