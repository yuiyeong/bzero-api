"""Socket.IO 데모 채팅 핸들러 (인증 불필요)"""
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results import ChatMessageResult
from bzero.core.redis import get_redis_client
from bzero.core.settings import get_settings
from bzero.domain.errors import RateLimitExceededError
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent
from bzero.presentation.api.dependencies import create_chat_message_service
from bzero.presentation.schemas.chat_message import SendMessageRequest
from bzero.presentation.socketio.dependencies import socket_handler
from bzero.presentation.socketio.server import get_socketio_server
from bzero.presentation.socketio.utils import (
    emit_new_message,
    emit_system_message,
    get_typed_session,
)


logger = logging.getLogger(__name__)
sio = get_socketio_server()

# 데모용 고정 룸 ID
DEMO_ROOM_ID = "00000000-0000-0000-0000-000000000000"
# 데모 네임스페이스
DEMO_NAMESPACE = "/demo"


@sio.on("join_room", namespace=DEMO_NAMESPACE)
@socket_handler(namespace=DEMO_NAMESPACE)
async def handle_join_room(sid: str, db_session: AsyncSession, data: dict[str, Any]):
    """데모 룸 참여."""
    logger.info(f"handle_join_room called - sid: {sid}")
    session = await get_typed_session(sio, sid, namespace=DEMO_NAMESPACE)

    # 1. Socket.IO 룸 입장
    await sio.enter_room(sid, DEMO_ROOM_ID, namespace=DEMO_NAMESPACE)
    logger.info(f"Demo user {session.user_id[:8]}... joined room {DEMO_ROOM_ID}")

    # 2. 입장 시스템 메시지
    chat_message_service = create_chat_message_service(db_session)
    system_message = await chat_message_service.create_system_message(
        room_id=Id.from_hex(DEMO_ROOM_ID),
        content=MessageContent(f"사용자 {session.user_id[:8]}... 님이 입장했습니다."),
    )

    await emit_system_message(
        sio,
        DEMO_ROOM_ID,
        ChatMessageResult.create_from(system_message),
        namespace=DEMO_NAMESPACE,
    )

    await db_session.commit()


@sio.on("send_message", namespace=DEMO_NAMESPACE)
@socket_handler(schema=SendMessageRequest, namespace=DEMO_NAMESPACE)
async def handle_send_message(
    sid: str, request: SendMessageRequest, db_session: AsyncSession
):
    """데모 메시지 전송 (DB 저장 없이 브로드캐스트만)."""
    session = await get_typed_session(sio, sid, namespace=DEMO_NAMESPACE)

    # 1. Rate Limiting 체크
    redis_client = get_redis_client()
    is_allowed = await redis_client.set(
        name=f"rate_limit:chat:{session.user_id}:{DEMO_ROOM_ID}",
        value="1",
        ex=2,
        nx=True,
    )

    if not is_allowed:
        raise RateLimitExceededError()

    # 2. 브로드캐스트 (DB 저장 없음)
    settings = get_settings()
    now = datetime.now(settings.timezone)

    # 데모용 임시 결과 객체 생성
    result = ChatMessageResult(
        message_id=str(uuid4()),
        room_id=DEMO_ROOM_ID,
        user_id=session.user_id,
        content=request.content,
        card_id=None,
        message_type="text",
        is_system=False,
        expires_at=now,
        created_at=now,
        updated_at=now,
    )

    await emit_new_message(sio, DEMO_ROOM_ID, result, namespace=DEMO_NAMESPACE)
    logger.debug(
        f"Demo message sent - user: {session.user_id[:8]}..., content: {request.content}"
    )
