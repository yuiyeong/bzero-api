"""Socket.IO 채팅 핸들러 (인증 필요)"""
import logging
from typing import Any

from bzero.application.use_cases.chat_messages import (
    GetMessageHistoryUseCase,
    SendMessageUseCase,
    ShareCardUseCase,
)
from bzero.core.redis import get_redis_client
from bzero.core.settings import get_settings
from bzero.domain.errors import BeZeroError
from bzero.domain.services import ChatMessageService, ConversationCardService, RoomStayService
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent
from bzero.infrastructure.adapters import RedisRateLimiter
from bzero.infrastructure.repositories.chat_message import SqlAlchemyChatMessageRepository
from bzero.infrastructure.repositories.conversation_card import SqlAlchemyConversationCardRepository
from bzero.infrastructure.repositories.room_stay import SqlAlchemyRoomStayRepository
from bzero.presentation.socketio.middleware import verify_jwt_token, verify_room_access
from bzero.presentation.socketio.server import get_socketio_server
from bzero.presentation.socketio.utils import get_db_session, get_session_data

logger = logging.getLogger(__name__)
sio = get_socketio_server()


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None):
    """클라이언트 연결 이벤트.

    Args:
        sid: Session ID (Socket.IO 자동 생성)
        environ: ASGI 환경 변수
        auth: 인증 데이터 {'token': 'jwt_token', 'room_id': 'room_id'}

    Returns:
        True: 연결 허용

    Raises:
        ConnectionRefusedError: 인증 실패, 권한 없음 등
    """
    try:
        # 1. 인증 데이터 확인
        if not auth:
            raise ConnectionRefusedError("No auth data provided")

        token = auth.get("token")
        room_id = auth.get("room_id")

        if not token or not room_id:
            raise ConnectionRefusedError("Missing token or room_id")

        # 2. JWT 토큰 검증
        payload = await verify_jwt_token(token)
        user_id = payload["sub"]

        # 3. 룸 접근 권한 검증
        async with get_db_session() as session:
            await verify_room_access(user_id, room_id, session)

        # 4. 세션 데이터 저장
        await sio.save_session(
            sid,
            {
                "user_id": user_id,
                "room_id": room_id,
            },
        )

        # 5. 룸에 참여
        sio.enter_room(sid, room_id)

        # 6. 입장 시스템 메시지 전송
        async with get_db_session() as session:
            chat_message_service = ChatMessageService(
                chat_message_repository=SqlAlchemyChatMessageRepository(session),
                rate_limiter=RedisRateLimiter(get_redis_client()),
                timezone=get_settings().timezone,
            )

            system_message = await chat_message_service.create_system_message(
                room_id=Id.from_hex(room_id),
                content=MessageContent("사용자가 입장했습니다."),
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
                room=room_id,
            )

        logger.info(f"User {user_id} connected to room {room_id} (sid: {sid})")
        return True

    except ValueError as e:
        logger.warning(f"Connection refused: {e}")
        raise ConnectionRefusedError(str(e))
    except Exception as e:
        logger.error(f"Connection error: {e}")
        raise ConnectionRefusedError("Internal server error")


@sio.event
async def disconnect(sid: str):
    """클라이언트 연결 해제 이벤트.

    Args:
        sid: Session ID
    """
    try:
        # 세션 데이터 조회
        session_data = await get_session_data(sio, sid)
        user_id = session_data["user_id"]
        room_id = session_data["room_id"]

        # 퇴장 시스템 메시지 전송
        async with get_db_session() as session:
            chat_message_service = ChatMessageService(
                chat_message_repository=SqlAlchemyChatMessageRepository(session),
                rate_limiter=RedisRateLimiter(get_redis_client()),
                timezone=get_settings().timezone,
            )

            system_message = await chat_message_service.create_system_message(
                room_id=Id.from_hex(room_id),
                content=MessageContent("사용자가 퇴장했습니다."),
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
                room=room_id,
            )

        # 룸에서 퇴장
        sio.leave_room(sid, room_id)

        logger.info(f"User {user_id} disconnected from room {room_id}")

    except Exception as e:
        logger.error(f"Disconnect error: {e}")


@sio.on("send_message")
async def handle_send_message(sid: str, data: dict[str, Any]):
    """텍스트 메시지 전송 이벤트.

    Args:
        sid: Session ID
        data: {'content': '메시지 내용'}
    """
    try:
        # 세션 데이터 조회
        session_data = await get_session_data(sio, sid)
        user_id = session_data["user_id"]
        room_id = session_data["room_id"]

        content = data.get("content")
        if not content:
            await sio.emit("error", {"error": "MISSING_CONTENT"}, to=sid)
            return

        # 메시지 전송 (기존 UseCase 100% 재사용)
        async with get_db_session() as session:
            chat_message_service = ChatMessageService(
                chat_message_repository=SqlAlchemyChatMessageRepository(session),
                rate_limiter=RedisRateLimiter(get_redis_client()),
                timezone=get_settings().timezone,
            )

            use_case = SendMessageUseCase(session, chat_message_service)
            result = await use_case.execute(user_id, room_id, content)

            # 룸 전체에 브로드캐스트
            await sio.emit(
                "new_message",
                {
                    "message": {
                        "message_id": result.message_id,
                        "user_id": result.user_id,
                        "content": result.content,
                        "message_type": result.message_type,
                        "created_at": result.created_at.isoformat(),
                    }
                },
                room=room_id,
            )

    except BeZeroError as e:
        await sio.emit("error", {"error": e.code.value}, to=sid)
    except Exception as e:
        logger.error(f"Send message error: {e}")
        await sio.emit("error", {"error": "INTERNAL_ERROR"}, to=sid)


@sio.on("share_card")
async def handle_share_card(sid: str, data: dict[str, Any]):
    """카드 공유 이벤트.

    Args:
        sid: Session ID
        data: {'card_id': '카드 ID'}
    """
    try:
        session_data = await get_session_data(sio, sid)
        user_id = session_data["user_id"]
        room_id = session_data["room_id"]

        card_id = data.get("card_id")
        if not card_id:
            await sio.emit("error", {"error": "MISSING_CARD_ID"}, to=sid)
            return

        async with get_db_session() as session:
            chat_message_service = ChatMessageService(
                chat_message_repository=SqlAlchemyChatMessageRepository(session),
                rate_limiter=RedisRateLimiter(get_redis_client()),
                timezone=get_settings().timezone,
            )
            conversation_card_service = ConversationCardService(
                conversation_card_repository=SqlAlchemyConversationCardRepository(session),
            )

            use_case = ShareCardUseCase(session, chat_message_service, conversation_card_service)
            result = await use_case.execute(user_id, room_id, card_id)

            await sio.emit(
                "new_message",
                {
                    "message": {
                        "message_id": result.message_id,
                        "user_id": result.user_id,
                        "content": result.content,
                        "card_id": result.card_id,
                        "message_type": result.message_type,
                        "created_at": result.created_at.isoformat(),
                    }
                },
                room=room_id,
            )

    except BeZeroError as e:
        await sio.emit("error", {"error": e.code.value}, to=sid)
    except Exception as e:
        logger.error(f"Share card error: {e}")
        await sio.emit("error", {"error": "INTERNAL_ERROR"}, to=sid)


@sio.on("get_history")
async def handle_get_history(sid: str, data: dict[str, Any]):
    """메시지 히스토리 조회 이벤트.

    Args:
        sid: Session ID
        data: {'cursor': '커서 (optional)', 'limit': 50}
    """
    try:
        session_data = await get_session_data(sio, sid)
        user_id = session_data["user_id"]
        room_id = session_data["room_id"]

        cursor = data.get("cursor")
        limit = data.get("limit", 50)

        async with get_db_session() as session:
            chat_message_service = ChatMessageService(
                chat_message_repository=SqlAlchemyChatMessageRepository(session),
                rate_limiter=RedisRateLimiter(get_redis_client()),
                timezone=get_settings().timezone,
            )
            room_stay_service = RoomStayService(
                room_stay_repository=SqlAlchemyRoomStayRepository(session),
            )

            use_case = GetMessageHistoryUseCase(chat_message_service, room_stay_service)
            results = await use_case.execute(user_id, room_id, cursor, limit)

            # 요청한 클라이언트에게만 응답
            await sio.emit(
                "history",
                {
                    "messages": [
                        {
                            "message_id": msg.message_id,
                            "user_id": msg.user_id,
                            "content": msg.content,
                            "card_id": msg.card_id,
                            "message_type": msg.message_type,
                            "is_system": msg.is_system,
                            "created_at": msg.created_at.isoformat(),
                        }
                        for msg in results
                    ]
                },
                to=sid,
            )

    except BeZeroError as e:
        await sio.emit("error", {"error": e.code.value}, to=sid)
    except Exception as e:
        logger.error(f"Get history error: {e}")
        await sio.emit("error", {"error": "INTERNAL_ERROR"}, to=sid)
