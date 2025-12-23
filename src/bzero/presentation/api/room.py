from fastapi import APIRouter

from bzero.application.use_cases.chat_messages.get_message_history import (
    GetMessageHistoryUseCase,
)
from bzero.application.use_cases.rooms.get_room_members import GetRoomMembersUseCase
from bzero.presentation.api.dependencies import (
    CurrentChatMessageService,
    CurrentJWTPayload,
    CurrentRoomStayService,
    CurrentUserService,
)
from bzero.presentation.schemas.chat_message import ChatMessageResponse
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


@router.get(
    "/{room_id}/messages",
    response_model=ListResponse[ChatMessageResponse],
    summary="채팅 히스토리 조회",
    description="룸의 채팅 메시지 히스토리를 cursor 기반 페이지네이션으로 조회합니다.",
)
async def get_room_history(
    room_id: str,
    jwt_payload: CurrentJWTPayload,
    chat_message_service: CurrentChatMessageService,
    room_stay_service: CurrentRoomStayService,
    cursor: str | None = None,
    limit: int = 50,
) -> ListResponse[ChatMessageResponse]:
    """채팅 메시지 히스토리를 조회합니다.

    Args:
        room_id: 방 ID (UUID v7 hex)
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        chat_message_service: 채팅 메시지 도메인 서비스
        room_stay_service: 체류 도메인 서비스
        cursor: 페이지네이션 커서 (이전 응답의 마지막 message_id)
        limit: 최대 조회 개수 (기본값: 50)

    Returns:
        ListResponse[ChatMessageResponse]: 메시지 목록
    """
    use_case = GetMessageHistoryUseCase(
        chat_message_service=chat_message_service,
        room_stay_service=room_stay_service,
    )
    results = await use_case.execute(
        user_id=jwt_payload.provider_user_id,
        room_id=room_id,
        cursor=cursor,
        limit=limit,
    )
    return ListResponse(
        list=[ChatMessageResponse.create_from(msg) for msg in results],
        pagination=Pagination(
            total=len(results),
            offset=0,  # Cursor 기반이므로 의미가 적지만 스키마 호환 유지
            limit=limit,
        ),
    )


# POST /cards 제거됨 (Socket.IO handle_share_card로 복원)
