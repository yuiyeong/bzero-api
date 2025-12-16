from fastapi import APIRouter

from bzero.application.use_cases.rooms.get_room_members import GetRoomMembersUseCase
from bzero.presentation.api.dependencies import (
    CurrentJWTPayload,
    CurrentRoomStayService,
    CurrentUserService,
)
from bzero.presentation.schemas.common import ListResponse, Pagination
from bzero.presentation.schemas.user import UserResponse


router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get(
    "/{room_id}/members",
    response_model=ListResponse[UserResponse],
    summary="같은 방 멤버 조회",
    description="현재 같은 방에 체류 중인 멤버 목록을 조회합니다.",
)
async def get_room_members(
    room_id: str,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    room_stay_service: CurrentRoomStayService,
) -> ListResponse[UserResponse]:
    """같은 방에 체류 중인 멤버 목록을 조회합니다.

    Args:
        room_id: 방 ID (UUID v7 hex)
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        user_service: 사용자 도메인 서비스
        room_stay_service: 체류 도메인 서비스

    Returns:
        ListResponse[UserResponse]: 같은 방 멤버 목록
    """
    use_case = GetRoomMembersUseCase(
        user_service=user_service,
        room_stay_service=room_stay_service,
    )
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        room_id=room_id,
    )
    return ListResponse(
        list=[UserResponse.create_from(user) for user in result.items],
        pagination=Pagination(total=result.total, offset=result.offset, limit=result.limit),
    )
