from fastapi import APIRouter

from bzero.application.use_cases.room_stays.get_current_stay import GetCurrentStayUseCase
from bzero.presentation.api.dependencies import (
    CurrentJWTPayload,
    CurrentRoomStayService,
    CurrentUserService,
)
from bzero.presentation.schemas.common import DataResponse
from bzero.presentation.schemas.room_stay import RoomStayResponse


router = APIRouter(prefix="/room-stays", tags=["room-stays"])


@router.get(
    "/current",
    response_model=DataResponse[RoomStayResponse] | None,
    summary="현재 체류 조회",
    description="현재 활성(CHECKED_IN) 체류 정보를 조회합니다.",
)
async def get_current_stay(
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    room_stay_service: CurrentRoomStayService,
) -> DataResponse[RoomStayResponse] | None:
    """현재 체류 정보를 조회합니다.

    Args:
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        user_service: 사용자 도메인 서비스
        room_stay_service: 체류 도메인 서비스

    Returns:
        RoomStayResponse: 현재 체류 정보 또는 None (체류 중이 아닌 경우)
    """
    use_case = GetCurrentStayUseCase(
        user_service=user_service,
        room_stay_service=room_stay_service,
    )
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
    )
    if result is None:
        return None
    return DataResponse(data=RoomStayResponse.create_from(result))
