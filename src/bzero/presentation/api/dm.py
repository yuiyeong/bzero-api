"""DM (1:1 대화) REST API 엔드포인트."""

from fastapi import APIRouter

from bzero.application.use_cases.dm import (
    AcceptDMRequestUseCase,
    GetDMHistoryUseCase,
    GetMyDMRoomsUseCase,
    RejectDMRequestUseCase,
    RequestDMUseCase,
)
from bzero.domain.services.direct_message import DirectMessageService
from bzero.domain.services.direct_message_room import DirectMessageRoomService
from bzero.domain.services.user import UserService
from bzero.presentation.api.dependencies import (
    CurrentJWTPayload,
    CurrentUserService,
    DBSession,
    create_dm_room_service,
    create_dm_service,
)
from bzero.presentation.schemas.common import ListResponse, Pagination
from bzero.presentation.schemas.dm import (
    CreateDMRequestRequest,
    DirectMessageResponse,
    DirectMessageRoomResponse,
)


router = APIRouter(prefix="/dm", tags=["dm"])



# =============================================================================
# Helper: 현재 사용자 ID 조회
# =============================================================================


from bzero.domain.value_objects import AuthProvider


async def get_current_user_id(
    jwt_payload: CurrentJWTPayload,
    user_service: UserService,
) -> str:
    """JWT 페이로드로부터 현재 사용자의 내부 ID를 조회합니다."""
    user = await user_service.get_or_create_user_by_provider(
        provider=AuthProvider(jwt_payload.provider),
        provider_user_id=jwt_payload.provider_user_id,
        email=jwt_payload.email,
    )
    return user.user_id.value.hex


# =============================================================================
# Command Endpoints (상태 변경)
# =============================================================================


@router.post(
    "/requests",
    response_model=DirectMessageRoomResponse,
    summary="1:1 대화 신청",
    description="같은 룸에 체류 중인 사용자에게 1:1 대화를 신청합니다.",
)
async def request_dm(
    request: CreateDMRequestRequest,
    session: DBSession,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
) -> DirectMessageRoomResponse:
    """1:1 대화를 신청합니다.

    Args:
        request: 대화 상대방 ID
        session: DB 세션
        jwt_payload: JWT 페이로드
        user_service: 사용자 서비스

    Returns:
        생성된 대화방 정보 (status: pending)

    Raises:
        NotInSameRoomError: 같은 룸에 체류 중이 아닌 경우
        DuplicatedDMRequestError: 이미 활성 대화방이 존재하는 경우
    """
    current_user_id = await get_current_user_id(jwt_payload, user_service)
    dm_room_service: DirectMessageRoomService = create_dm_room_service(session)

    use_case = RequestDMUseCase(session, dm_room_service)
    result = await use_case.execute(
        requester_id=current_user_id,
        target_id=request.to_user_id,
    )

    return DirectMessageRoomResponse.create_from(result)


@router.post(
    "/requests/{dm_room_id}/accept",
    response_model=DirectMessageRoomResponse,
    summary="1:1 대화 수락",
    description="대화 신청을 수락합니다. 수신자(user2)만 수락할 수 있습니다.",
)
async def accept_dm_request(
    dm_room_id: str,
    session: DBSession,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
) -> DirectMessageRoomResponse:
    """대화 신청을 수락합니다.

    Args:
        dm_room_id: 대화방 ID
        session: DB 세션
        jwt_payload: JWT 페이로드
        user_service: 사용자 서비스

    Returns:
        업데이트된 대화방 정보 (status: accepted)

    Raises:
        NotFoundDMRoomError: 대화방을 찾을 수 없는 경우
        ForbiddenDMRoomAccessError: 수락 권한이 없는 경우
        InvalidDMRoomStatusError: PENDING 상태가 아닌 경우
    """
    current_user_id = await get_current_user_id(jwt_payload, user_service)
    dm_room_service: DirectMessageRoomService = create_dm_room_service(session)

    use_case = AcceptDMRequestUseCase(session, dm_room_service)
    result = await use_case.execute(
        dm_room_id=dm_room_id,
        user_id=current_user_id,
    )

    return DirectMessageRoomResponse.create_from(result)


@router.post(
    "/requests/{dm_room_id}/reject",
    response_model=DirectMessageRoomResponse,
    summary="1:1 대화 거절",
    description="대화 신청을 거절합니다. 수신자(user2)만 거절할 수 있습니다.",
)
async def reject_dm_request(
    dm_room_id: str,
    session: DBSession,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
) -> DirectMessageRoomResponse:
    """대화 신청을 거절합니다.

    Args:
        dm_room_id: 대화방 ID
        session: DB 세션
        jwt_payload: JWT 페이로드
        user_service: 사용자 서비스

    Returns:
        업데이트된 대화방 정보 (status: rejected)

    Raises:
        NotFoundDMRoomError: 대화방을 찾을 수 없는 경우
        ForbiddenDMRoomAccessError: 거절 권한이 없는 경우
        InvalidDMRoomStatusError: PENDING 상태가 아닌 경우
    """
    current_user_id = await get_current_user_id(jwt_payload, user_service)
    dm_room_service: DirectMessageRoomService = create_dm_room_service(session)

    use_case = RejectDMRequestUseCase(session, dm_room_service)
    result = await use_case.execute(
        dm_room_id=dm_room_id,
        user_id=current_user_id,
    )

    return DirectMessageRoomResponse.create_from(result)


# =============================================================================
# Query Endpoints (조회)
# =============================================================================


@router.get(
    "/rooms",
    response_model=ListResponse[DirectMessageRoomResponse],
    summary="내 대화방 목록 조회",
    description="내가 참여 중인 1:1 대화방 목록을 조회합니다.",
)
async def get_my_dm_rooms(
    session: DBSession,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> ListResponse[DirectMessageRoomResponse]:
    """내 대화방 목록을 조회합니다.

    Args:
        session: DB 세션
        jwt_payload: JWT 페이로드
        user_service: 사용자 서비스
        status: 상태 필터 (pending, accepted, active, rejected, ended)
        limit: 최대 조회 개수 (기본값: 20)
        offset: 오프셋 (기본값: 0)

    Returns:
        대화방 목록 (최근 업데이트 순)
    """
    current_user_id = await get_current_user_id(jwt_payload, user_service)
    dm_room_service: DirectMessageRoomService = create_dm_room_service(session)
    dm_service: DirectMessageService = create_dm_service(session)

    use_case = GetMyDMRoomsUseCase(session, dm_room_service, dm_service)
    results = await use_case.execute(
        user_id=current_user_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return ListResponse(
        list=[DirectMessageRoomResponse.create_from(r) for r in results],
        pagination=Pagination(total=len(results), offset=offset, limit=limit),
    )


@router.get(
    "/rooms/{dm_room_id}/messages",
    response_model=ListResponse[DirectMessageResponse],
    summary="대화 메시지 조회",
    description="1:1 대화방의 메시지 히스토리를 조회합니다. 조회 시 읽음 처리됩니다.",
)
async def get_dm_messages(
    dm_room_id: str,
    session: DBSession,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    cursor: str | None = None,
    limit: int = 50,
) -> ListResponse[DirectMessageResponse]:
    """대화 메시지 히스토리를 조회합니다.

    Args:
        dm_room_id: 대화방 ID
        session: DB 세션
        jwt_payload: JWT 페이로드
        user_service: 사용자 서비스
        cursor: 페이지네이션 커서 (이전 응답의 마지막 dm_id)
        limit: 최대 조회 개수 (기본값: 50)

    Returns:
        메시지 목록 (오래된 순)

    Raises:
        NotFoundDMRoomError: 대화방을 찾을 수 없는 경우
        ForbiddenDMRoomAccessError: 참여자가 아닌 경우
    """
    current_user_id = await get_current_user_id(jwt_payload, user_service)
    dm_room_service: DirectMessageRoomService = create_dm_room_service(session)
    dm_service: DirectMessageService = create_dm_service(session)

    use_case = GetDMHistoryUseCase(session, dm_room_service, dm_service)
    results = await use_case.execute(
        dm_room_id=dm_room_id,
        user_id=current_user_id,
        cursor=cursor,
        limit=limit,
        mark_as_read=True,
    )

    return ListResponse(
        list=[DirectMessageResponse.create_from(r) for r in results],
        pagination=Pagination(total=len(results), offset=0, limit=limit),
    )
