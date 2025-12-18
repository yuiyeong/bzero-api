"""Socket.IO 데모 채팅 핸들러 (인증 불필요)"""
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from bzero.core.redis import get_redis_client
from bzero.core.settings import get_settings
from bzero.domain.services import ChatMessageService
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent
from bzero.infrastructure.adapters import RedisRateLimiter
from bzero.infrastructure.repositories.chat_message import SqlAlchemyChatMessageRepository
from bzero.presentation.socketio.server import get_socketio_server
from bzero.presentation.socketio.utils import get_db_session, get_session_data

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

        # 룸에 참여
        sio.enter_room(sid, DEMO_ROOM_ID, namespace=DEMO_NAMESPACE)

        # 클라이언트에게 user_id 전송
        await sio.emit(
            "connected",
            {"user_id": user_id},
            to=sid,
            namespace=DEMO_NAMESPACE,
        )

        # 입장 시스템 메시지
        async with get_db_session() as session:
            chat_message_service = ChatMessageService(
                chat_message_repository=SqlAlchemyChatMessageRepository(session),
                rate_limiter=RedisRateLimiter(get_redis_client()),
                timezone=get_settings().timezone,
            )

            system_message = await chat_message_service.create_system_message(
                room_id=Id.from_hex(DEMO_ROOM_ID),
                content=MessageContent(f"사용자 {user_id[:8]}... 님이 입장했습니다."),
            )

            await sio.emit(
                "system_message",
                {
                    "message": {
                        "message_id": system_message.message_id.to_hex(),
                        "content": system_message.content.value,
                        "created_at": system_message.created_at.isoformat(),
                    }
                },
                room=DEMO_ROOM_ID,
                namespace=DEMO_NAMESPACE,
            )

        logger.info(f"Demo user {user_id} connected (sid: {sid})")
        return True

    except Exception as e:
        logger.error(f"Demo connection error: {e}")
        return False


@sio.event(namespace=DEMO_NAMESPACE)
async def disconnect(sid: str):
    """데모 연결 해제.

    Args:
        sid: Session ID
    """
    try:
        session_data = await get_session_data(sio, sid, namespace=DEMO_NAMESPACE)
        user_id = session_data["user_id"]

        # 퇴장 시스템 메시지
        async with get_db_session() as session:
            chat_message_service = ChatMessageService(
                chat_message_repository=SqlAlchemyChatMessageRepository(session),
                rate_limiter=RedisRateLimiter(get_redis_client()),
                timezone=get_settings().timezone,
            )

            system_message = await chat_message_service.create_system_message(
                room_id=Id.from_hex(DEMO_ROOM_ID),
                content=MessageContent(f"사용자 {user_id[:8]}... 님이 퇴장했습니다."),
            )

            await sio.emit(
                "system_message",
                {
                    "message": {
                        "message_id": system_message.message_id.to_hex(),
                        "content": system_message.content.value,
                        "created_at": system_message.created_at.isoformat(),
                    }
                },
                room=DEMO_ROOM_ID,
                namespace=DEMO_NAMESPACE,
            )

        sio.leave_room(sid, DEMO_ROOM_ID, namespace=DEMO_NAMESPACE)
        logger.info(f"Demo user {user_id} disconnected")

    except Exception as e:
        logger.error(f"Demo disconnect error: {e}")


@sio.on("join_room", namespace="/demo")
async def handle_join_room(sid, data):
    # data는 클라이언트가 보낸 JSON 객체입니다. (예: {'room_id': '...'})
    room_id = data.get("room_id")
    
    if room_id:
        # 핵심 기능: 해당 sid를 room_id 그룹에 넣습니다.
        await sio.enter_room(sid, room_id, namespace=DEMO_NAMESPACE)
        
        print(f"✅ User {sid} joined room: {room_id}")
        
        # (선택 사항) 같은 방에 있는 다른 사람들에게 입장 알림
        await sio.emit(
            "system_message", 
            {"content": "새로운 사용자가 입장했습니다."}, 
            room=room_id, 
            namespace=DEMO_NAMESPACE
        )
    else:
        print(f"⚠️ User {sid} tried to join without room_id")


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
            await sio.emit("error", {"error": "MISSING_CONTENT"}, to=sid, namespace=DEMO_NAMESPACE)
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
            await sio.emit("error", {"error": "RATE_LIMIT_EXCEEDED"}, to=sid, namespace=DEMO_NAMESPACE)
            return

        # 브로드캐스트 (DB 저장 없음)
        settings = get_settings()
        now = datetime.now(settings.timezone)

        await sio.emit(
            "new_message",
            {
                "message": {
                    "message_id": str(uuid4()),
                    "user_id": user_id,
                    "content": content,
                    "message_type": "text",
                    "created_at": now.isoformat(),
                }
            },
            room=DEMO_ROOM_ID,
            namespace=DEMO_NAMESPACE,
        )
        logger.error(f"Demo send message content: {content}")
    except Exception as e:
        logger.error(f"Demo send message error: {e}")
        await sio.emit("error", {"error": "INTERNAL_ERROR"}, to=sid, namespace=DEMO_NAMESPACE)
