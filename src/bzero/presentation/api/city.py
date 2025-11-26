"""도시 관련 API 엔드포인트."""

from fastapi import APIRouter

from bzero.application.use_cases.cities.get_active_cities import (
    GetActiveCitiesUseCase,
)
from bzero.application.use_cases.cities.get_city_by_id import GetCityByIdUseCase
from bzero.presentation.api.dependencies import CurrentCityService
from bzero.presentation.schemas.city import CityResponse
from bzero.presentation.schemas.common import DataResponse

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get(
    "",
    response_model=DataResponse[list[CityResponse]],
    summary="활성 도시 목록 조회",
    description="활성화된 도시 목록을 display_order 순서대로 조회합니다.",
)
async def get_active_cities(
    city_service: CurrentCityService,
) -> DataResponse[list[CityResponse]]:
    """활성화된 도시 목록 조회.

    - is_active=True인 도시만 반환
    - display_order 오름차순 정렬
    """
    results = await GetActiveCitiesUseCase(city_service).execute()
    return DataResponse(data=[CityResponse.create_from(result) for result in results])


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
