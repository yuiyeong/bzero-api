import logging
from typing import Any

import socketio
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results import ChatMessageResult
from bzero.domain.errors import (
    AccessDeniedError,
    BadRequestError,
    BeZeroError,
    NotFoundError,
    RateLimitExceededError,
    UnauthorizedError,
)
from bzero.domain.value_objects import Id
from bzero.presentation.api.dependencies import create_room_stay_service
from bzero.presentation.socketio.error_codes import SocketIOErrorCode

logger = logging.getLogger(__name__)


async def get_session_data(
    sio: socketio.AsyncServer, sid: str, namespace: str = "/"
) -> dict[str, Any]:
    """세션 데이터를 조회하고 검증합니다.

    Args:
        sio: Socket.IO 서버 인스턴스
        sid: Session ID
        namespace: 네임스페이스 (기본값: "/")

    Returns:
        세션 데이터 (user_id, room_id 포함)

    Raises:
        ValueError: 세션 데이터가 없거나 유효하지 않은 경우
    """
    session_data = await sio.get_session(sid, namespace=namespace)

    if not session_data:
        raise ValueError("No session data")

    if "user_id" not in session_data or "room_id" not in session_data:
        raise ValueError("Invalid session data")

    return session_data


async def verify_room_access(
    user_id: str, room_id: str, session: AsyncSession, room_stay_service=None
) -> None:
    """사용자가 해당 룸에 접근 권한이 있는지 검증합니다.

    Args:
        user_id: 사용자 ID (hex)
        room_id: 룸 ID (hex)
        session: DB 세션
        room_stay_service: RoomStay 서비스 (선택적, 제공되지 않으면 자동 생성)

    Raises:
        ValueError: 접근 권한이 없는 경우
    """
    if room_stay_service is None:
        room_stay_service = create_room_stay_service(session)

    try:
        await room_stay_service.get_stays_by_user_id_and_room_id(
            user_id=Id.from_hex(user_id),
            room_id=Id.from_hex(room_id),
        )
    except BeZeroError as e:
        raise ValueError(f"Access denied: {e.code.value}") from e


async def handle_socketio_error(
    sio: socketio.AsyncServer,
    sid: str,
    error: Exception,
    namespace: str = "/",
) -> None:
    """도메인 에러를 Socket.IO 에러 응답으로 변환하여 전송합니다.

    Args:
        sio: Socket.IO 서버 인스턴스
        sid: Session ID
        error: 발생한 예외
        namespace: 네임스페이스
    """
    if isinstance(error, RateLimitExceededError):
        code = SocketIOErrorCode.RATE_LIMIT_EXCEEDED
    elif isinstance(error, UnauthorizedError):
        code = SocketIOErrorCode.UNAUTHORIZED
    elif isinstance(error, AccessDeniedError):
        code = SocketIOErrorCode.FORBIDDEN
    elif isinstance(error, NotFoundError):
        code = SocketIOErrorCode.NOT_FOUND
    elif isinstance(error, BadRequestError):
        code = SocketIOErrorCode.INVALID_PARAMETER
    elif isinstance(error, BeZeroError):
        code = SocketIOErrorCode.INTERNAL_ERROR
    else:
        logger.exception(f"Unexpected error in Socket.IO handler: {error}")
        code = SocketIOErrorCode.INTERNAL_ERROR

    await sio.emit("error", {"error": code.value}, to=sid, namespace=namespace)


async def emit_system_message(
    sio: socketio.AsyncServer,
    room_id: str,
    result: ChatMessageResult,
    namespace: str = "/",
) -> None:
    """시스템 메시지를 룸에 브로드캐스트합니다."""
    await sio.emit(
        "system_message",
        {"message": result.to_dict()},
        room=room_id,
        namespace=namespace,
    )


async def emit_new_message(
    sio: socketio.AsyncServer,
    room_id: str,
    result: ChatMessageResult,
    namespace: str = "/",
) -> None:
    """새 메시지(일반/카드)를 룸에 브로드캐스트합니다."""
    await sio.emit(
        "new_message",
        {"message": result.to_dict()},
        room=room_id,
        namespace=namespace,
    )
