import logging
from typing import Any

import socketio
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results import ChatMessageResult
from bzero.domain.errors import (
    AccessDeniedError,
    BadRequestError,
    BeZeroError,
    ErrorCode,
    NotFoundError,
    RateLimitExceededError,
    UnauthorizedError,
)
from bzero.domain.value_objects import Id
from bzero.presentation.api.dependencies import create_room_stay_service
from bzero.presentation.schemas.chat_message import ChatMessageResponse
from bzero.presentation.schemas.socketio import SocketSession

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


async def get_typed_session(
    sio: socketio.AsyncServer, sid: str, namespace: str = "/"
) -> SocketSession:
    """세션 데이터를 SocketSession 모델로 반환합니다."""
    data = await get_session_data(sio, sid, namespace=namespace)
    return SocketSession.model_validate(data)


async def handle_socketio_error(
    sio: socketio.AsyncServer,
    sid: str,
    error: Exception,
    namespace: str = "/",
) -> None:
    """도메인 에러를 Socket.IO 에러 응답으로 변환하여 전송합니다."""
    if isinstance(error, RateLimitExceededError):
        code = ErrorCode.RATE_LIMIT_EXCEEDED
    elif isinstance(error, UnauthorizedError):
        code = ErrorCode.UNAUTHORIZED
    elif isinstance(error, AccessDeniedError):
        code = ErrorCode.FORBIDDEN_ROOM_FOR_USER
    elif isinstance(error, NotFoundError):
        code = ErrorCode.INVALID_PARAMETER  # Generic Not Found
    elif isinstance(error, BadRequestError):
        code = ErrorCode.INVALID_PARAMETER
    elif isinstance(error, ValueError) and "Room ID mismatch" in str(error):
        code = ErrorCode.ROOM_ID_MISMATCH
    elif isinstance(error, BeZeroError):
        code = error.code
    else:
        logger.exception(f"Unexpected error in Socket.IO handler: {error}")
        code = ErrorCode.INTERNAL_ERROR

    # ErrorCode.name을 클라이언트에 전송하여 일관성 유지
    await sio.emit("error", {"error": code.name}, to=sid, namespace=namespace)


async def emit_system_message(
    sio: socketio.AsyncServer,
    room_id: str,
    result: ChatMessageResult,
    namespace: str = "/",
) -> None:
    """시스템 메시지를 룸에 브로드캐스트합니다."""
    response = ChatMessageResponse.create_from(result)
    await sio.emit(
        "system_message",
        {"message": response.model_dump(mode="json")},
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
    response = ChatMessageResponse.create_from(result)
    await sio.emit(
        "new_message",
        {"message": response.model_dump(mode="json")},
        room=room_id,
        namespace=namespace,
    )
