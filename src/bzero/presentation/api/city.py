"""도시 관련 API 엔드포인트."""

from typing import Annotated

from fastapi import APIRouter, Query

from bzero.application.use_cases.cities.get_active_cities import (
    GetActiveCitiesUseCase,
)
from bzero.application.use_cases.cities.get_city_by_id import GetCityByIdUseCase
from bzero.presentation.api.dependencies import CurrentCityService
from bzero.presentation.schemas.city import CityResponse
from bzero.presentation.schemas.common import DataResponse, ListResponse, Pagination

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get(
    "",
    response_model=ListResponse[CityResponse],
    summary="활성 도시 목록 조회",
    description="활성화된 도시 목록을 display_order 순서대로 조회합니다.",
)
async def get_active_cities(
    city_service: CurrentCityService,
    offset: Annotated[int, Query(ge=0, description="조회 시작 위치")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="조회할 최대 개수")] = 20,
) -> ListResponse[CityResponse]:
    """활성화된 도시 목록 조회.

    - is_active=True인 도시만 반환
    - display_order 오름차순 정렬
    - pagination 지원 (기본값: offset=0, limit=20)
    """
    result = await GetActiveCitiesUseCase(city_service).execute(offset, limit)
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
