"""Socket.IO 데모 채팅 핸들러 (인증 불필요)"""
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from bzero.core.database import get_async_db_session
from bzero.core.redis import get_redis_client
from bzero.core.settings import get_settings
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent
from bzero.application.results import ChatMessageResult
from bzero.presentation.api.dependencies import create_chat_message_service
from bzero.presentation.socketio.error_codes import SocketIOErrorCode
from bzero.presentation.socketio.server import get_socketio_server
from bzero.presentation.socketio.utils import (
    emit_new_message,
    emit_system_message,
    get_session_data,
    handle_socketio_error,
)


logger = logging.getLogger(__name__)
sio = get_socketio_server()

# 데모용 고정 룸 ID
DEMO_ROOM_ID = "00000000-0000-0000-0000-000000000000"
# 데모 네임스페이스
DEMO_NAMESPACE = "/demo"


@sio.event(namespace=DEMO_NAMESPACE)
async def connect(sid: str, environ: dict):
    """데모 연결 (인증 없음).

    임시 user_id를 생성하여 데모 룸에 참여합니다.

    Args:
        sid: Session ID
        environ: ASGI 환경 변수

    Returns:
        True: 연결 허용
    """
    try:
        # 임시 사용자 ID 생성
        user_id = str(uuid4())

        # 세션 데이터 저장
        await sio.save_session(
            sid,
            {
                "user_id": user_id,
                "room_id": DEMO_ROOM_ID,
            },
            namespace=DEMO_NAMESPACE,
        )

        # 클라이언트에게 user_id 전송
        await sio.emit(
            "connected",
            {"user_id": user_id},
            to=sid,
            namespace=DEMO_NAMESPACE,
        )

        logger.info(f"Demo user {user_id} authenticated (sid: {sid})")
        return True

    except Exception as e:
        logger.error(f"Demo connection error: {e}")
        return False


@sio.event(namespace=DEMO_NAMESPACE)
async def disconnect(sid: str, reason: Any = None):
    """데모 연결 해제.

    Args:
        sid: Session ID
    """
    try:
        session_data = await get_session_data(sio, sid, namespace=DEMO_NAMESPACE)
        user_id = session_data["user_id"]

        # 퇴장 시스템 메시지
        async with get_async_db_session() as session:
            chat_message_service = create_chat_message_service(session)

            system_message = await chat_message_service.create_system_message(
                room_id=Id.from_hex(DEMO_ROOM_ID),
                content=MessageContent(f"사용자 {user_id[:8]}... 님이 퇴장했습니다."),
            )

            await emit_system_message(
                sio, DEMO_ROOM_ID, ChatMessageResult.create_from(system_message), namespace=DEMO_NAMESPACE
            )

            await session.commit()

        sio.leave_room(sid, DEMO_ROOM_ID, namespace=DEMO_NAMESPACE)
        logger.info(f"Demo user {user_id} disconnected")

    except Exception as e:
        await handle_socketio_error(sio, sid, e, namespace=DEMO_NAMESPACE)


@sio.on("join_room", namespace=DEMO_NAMESPACE)
async def handle_join_room(sid: str, data: dict[str, Any]):
    # data는 클라이언트가 보낸 JSON 객체입니다. (예: {'room_id': '...'})
    room_id = data.get("room_id")
    session_data = await get_session_data(sio, sid, namespace=DEMO_NAMESPACE)
    user_id = session_data["user_id"]
    if room_id != session_data["room_id"]:
        await sio.emit("error", {"error": SocketIOErrorCode.ROOM_ID_MISMATCH.value}, to=sid, namespace=DEMO_NAMESPACE)
        return
    try:
        # 핵심 기능: 해당 sid를 room_id 그룹에 넣습니다.
        await sio.enter_room(sid, room_id, namespace=DEMO_NAMESPACE)

        logger.info(f"Demo user {user_id[:8]}... joined room {room_id}")

        # 입장 시스템 메시지
        async with get_async_db_session() as session:
            chat_message_service = create_chat_message_service(session)

            system_message = await chat_message_service.create_system_message(
                room_id=Id.from_hex(room_id),
                content=MessageContent(f"사용자 {user_id[:8]}... 님이 입장했습니다."),
            )

            await emit_system_message(
                sio, room_id, ChatMessageResult.create_from(system_message), namespace=DEMO_NAMESPACE
            )

            await session.commit()
    except Exception as e:
        await handle_socketio_error(sio, sid, e, namespace=DEMO_NAMESPACE)


@sio.on("send_message", namespace=DEMO_NAMESPACE)
async def handle_send_message(sid: str, data: dict[str, Any]):
    """데모 메시지 전송 (DB 저장 없이 브로드캐스트만).

    Args:
        sid: Session ID
        data: {'content': '메시지 내용'}
    """
    try:
        session_data = await get_session_data(sio, sid, namespace=DEMO_NAMESPACE)
        user_id = session_data["user_id"]

        content = data.get("content")
        if not content:
            await sio.emit("error", {"error": SocketIOErrorCode.MISSING_CONTENT.value}, to=sid, namespace=DEMO_NAMESPACE)
            return

        # Rate Limiting 체크
        redis_client = get_redis_client()
        is_allowed = await redis_client.set(
            name=f"rate_limit:chat:{user_id}:{DEMO_ROOM_ID}",
            value="1",
            ex=2,
            nx=True,
        )

        if not is_allowed:
            await sio.emit("error", {"error": SocketIOErrorCode.RATE_LIMIT_EXCEEDED.value}, to=sid, namespace=DEMO_NAMESPACE)
            return

        # 브로드캐스트 (DB 저장 없음)
        settings = get_settings()
        now = datetime.now(settings.timezone)
        
        # 데모용 임시 결과 객체 생성
        result = ChatMessageResult(
            message_id=str(uuid4()),
            room_id=DEMO_ROOM_ID,
            user_id=user_id,
            content=content,
            card_id=None,
            message_type="text",
            is_system=False,
            expires_at=now,  # 데모는 만료 없음
            created_at=now,
            updated_at=now,
        )

        await emit_new_message(sio, DEMO_ROOM_ID, result, namespace=DEMO_NAMESPACE)
        logger.debug(f"Demo message sent - user: {user_id[:8]}..., content: {content}")
    except Exception as e:
        await handle_socketio_error(sio, sid, e, namespace=DEMO_NAMESPACE)
