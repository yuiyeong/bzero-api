"""도시 관련 API 엔드포인트."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from bzero.application.use_cases.cities.create_city import CreateCityUseCase
from bzero.application.use_cases.cities.get_cities import (
    GetCitiesUseCase,
)
from bzero.application.use_cases.cities.get_city_by_id import GetCityByIdUseCase
from bzero.presentation.api.dependencies import (
    AdminKeyVerified,
    CurrentCityService,
    DBSession,
)
from bzero.presentation.schemas.city import CityCreateRequest, CityResponse
from bzero.presentation.schemas.common import DataResponse, ListResponse, Pagination


router = APIRouter(prefix="/cities", tags=["cities"])


@router.post(
    "",
    response_model=DataResponse[CityResponse],
    status_code=status.HTTP_201_CREATED,
    summary="도시 생성 (Admin)",
    description="새로운 도시를 생성합니다. is_active=false로 생성하면 Coming Soon 도시가 됩니다. X-Admin-Key 헤더 필수.",
)
async def create_city(
    request: CityCreateRequest,
    city_service: CurrentCityService,
    session: DBSession,
    _admin_verified: AdminKeyVerified,
) -> DataResponse[CityResponse]:
    """도시 생성 (Admin).

    - X-Admin-Key 헤더로 인증 필요
    - is_active=false: Coming Soon 도시 (터미널에서 비활성 상태로 표시)
    - is_active=true: 활성 도시 (티켓 예매 가능)
    """
    result = await CreateCityUseCase(city_service, session).execute(
        name=request.name,
        theme=request.theme,
        description=request.description,
        image_url=request.image_url,
        base_cost_points=request.base_cost_points,
        base_duration_hours=request.base_duration_hours,
        is_active=request.is_active,
        display_order=request.display_order,
    )
    return DataResponse(data=CityResponse.create_from(result))


@router.get(
    "",
    response_model=ListResponse[CityResponse],
    summary="도시 목록 조회",
    description="도시 목록을 display_order 순서대로 조회합니다.",
)
async def get_cities(
    city_service: CurrentCityService,
    offset: Annotated[int, Query(ge=0, description="조회 시작 위치")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="조회할 최대 개수")] = 20,
    include_inactive: Annotated[bool, Query(description="비활성화된 도시 포함 여부")] = False,
) -> ListResponse[CityResponse]:
    """도시 목록 조회.

    - include_inactive=False(기본값): 활성화된 도시만 조회
    - include_inactive=True: 비활성화된 도시 포함 조회
    - display_order 오름차순 정렬
    - pagination 지원
    """
    result = await GetCitiesUseCase(city_service).execute(
        offset=offset,
        limit=limit,
        active_only=not include_inactive,
    )
    return ListResponse(
        list=[CityResponse.create_from(city) for city in result.items],
        pagination=Pagination(total=result.total, offset=result.offset, limit=result.limit),
    )


@router.get(
    "/{city_id}",
    response_model=DataResponse[CityResponse],
    summary="도시 상세 정보 조회",
    description="도시 ID로 특정 도시의 상세 정보를 조회합니다.",
)
async def get_city_by_id(
    city_id: str,
    city_service: CurrentCityService,
) -> DataResponse[CityResponse]:
    """도시 상세 정보 조회.

    Args:
        city_id: 도시 ID (UUID hex 문자열)

    Returns:
        도시 상세 정보

    Raises:
        HTTPException 404: 도시를 찾을 수 없는 경우
    """
    result = await GetCityByIdUseCase(city_service).execute(city_id)
    return DataResponse(data=CityResponse.create_from(result))
