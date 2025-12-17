"""채팅 WebSocket API.

실시간 채팅 메시지 전송/수신을 위한 WebSocket 엔드포인트를 제공합니다.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.use_cases.chat_messages import (
    GetMessageHistoryUseCase,
    GetRandomCardUseCase,
    SendMessageUseCase,
    ShareCardUseCase,
)
from bzero.core.database import get_async_db_session
from bzero.core.redis import get_redis_client
from bzero.core.settings import get_settings
from bzero.domain.errors import BeZeroError
from bzero.domain.services import ChatMessageService, ConversationCardService, RoomStayService
from bzero.domain.value_objects.chat_message import MessageContent
from bzero.infrastructure.adapters import RedisRateLimiter
from bzero.infrastructure.auth.jwt_utils import verify_supabase_jwt
from bzero.infrastructure.repositories.chat_message import SqlAlchemyChatMessageRepository
from bzero.infrastructure.repositories.conversation_card import SqlAlchemyConversationCardRepository
from bzero.infrastructure.repositories.room_stay import SqlAlchemyRoomStayRepository
from bzero.presentation.websocket import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# 전역 ConnectionManager (싱글톤)
connection_manager = ConnectionManager(timezone=get_settings().timezone)


async def verify_websocket_token(token: str) -> dict:
    """WebSocket 연결 시 JWT 토큰을 검증합니다.

    Args:
        token: JWT 토큰

    Returns:
        JWT 페이로드 (sub, email 등)

    Raises:
        ValueError: 토큰 검증 실패 시
    """
    settings = get_settings()
    try:
        return verify_supabase_jwt(
            token=token,
            secret=settings.auth.supabase_jwt_secret.get_secret_value(),
            audience=settings.auth.supabase_jwt_audience,
        )
    except Exception as e:
        logger.error(f"WebSocket JWT verification failed: {e}")
        raise ValueError("Invalid token") from e


@router.websocket("/rooms/{room_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str,
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
):
    """WebSocket 채팅 엔드포인트.

    URL: /ws/chat/rooms/{room_id}?token={jwt_token}

    메시지 형식:
        - 클라이언트 → 서버:
            - {"type": "ping"} - 하트비트
            - {"type": "send_message", "content": "..."} - 텍스트 메시지 전송
            - {"type": "share_card", "card_id": "..."} - 카드 공유
            - {"type": "get_history", "cursor": "...", "limit": 50} - 메시지 히스토리 조회

        - 서버 → 클라이언트:
            - {"type": "pong"} - 하트비트 응답
            - {"type": "new_message", "message": {...}} - 새 메시지 (브로드캐스트)
            - {"type": "system_message", "message": {...}} - 시스템 메시지
            - {"type": "history", "messages": [...]} - 메시지 히스토리
            - {"type": "error", "error": "..."} - 에러 메시지

    Args:
        websocket: WebSocket 연결
        room_id: 룸 ID (hex 문자열)
        token: JWT 인증 토큰 (쿼리 파라미터)
        session: 데이터베이스 세션
    """
    # 1. JWT 토큰 검증
    try:
        payload = await verify_websocket_token(token)
        user_id = payload["sub"]
    except ValueError:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    # 2. 서비스 인스턴스 생성
    redis_client = get_redis_client()
    settings = get_settings()

    chat_message_service = ChatMessageService(
        chat_message_repository=SqlAlchemyChatMessageRepository(session),
        rate_limiter=RedisRateLimiter(redis_client),
        timezone=settings.timezone,
    )
    conversation_card_service = ConversationCardService(
        conversation_card_repository=SqlAlchemyConversationCardRepository(session),
    )
    room_stay_service = RoomStayService(
        room_stay_repository=SqlAlchemyRoomStayRepository(session),
    )

    # 3. 사용자가 해당 룸에 체류 중인지 검증
    try:
        from bzero.domain.value_objects import Id

        await room_stay_service.get_stays_by_user_id_and_room_id(
            user_id=Id.from_hex(user_id),
            room_id=Id.from_hex(room_id),
        )
    except BeZeroError as e:
        await websocket.close(code=1008, reason=e.code.value)
        return

    # 4. WebSocket 연결
    await connection_manager.connect(room_id, user_id, websocket)

    # 5. 입장 시스템 메시지 전송
    try:
        system_message = await chat_message_service.create_system_message(
            room_id=Id.from_hex(room_id),
            content=MessageContent("사용자가 입장했습니다."),
        )
        await session.commit()

        # 룸 전체에 브로드캐스트
        await connection_manager.broadcast_to_room(
            message={
                "type": "system_message",
                "message": {
                    "message_id": system_message.message_id.to_hex(),
                    "content": system_message.content.value,
                    "created_at": system_message.created_at.isoformat(),
                },
            },
            room_id=room_id,
        )
    except Exception as e:
        logger.error(f"Failed to send join system message: {e}")

    # 6. 메시지 수신 루프
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "ping":
                # 하트비트 업데이트
                connection_manager.update_heartbeat(user_id)
                await websocket.send_json({"type": "pong"})

            elif message_type == "send_message":
                # 텍스트 메시지 전송
                try:
                    use_case = SendMessageUseCase(session, chat_message_service)
                    result = await use_case.execute(
                        user_id=user_id,
                        room_id=room_id,
                        content=data["content"],
                    )

                    # 룸 전체에 브로드캐스트
                    await connection_manager.broadcast_to_room(
                        message={
                            "type": "new_message",
                            "message": {
                                "message_id": result.message_id,
                                "user_id": result.user_id,
                                "content": result.content,
                                "message_type": result.message_type,
                                "created_at": result.created_at.isoformat(),
                            },
                        },
                        room_id=room_id,
                    )
                except BeZeroError as e:
                    await websocket.send_json({"type": "error", "error": e.code.value})

            elif message_type == "share_card":
                # 카드 공유
                try:
                    use_case = ShareCardUseCase(session, chat_message_service, conversation_card_service)
                    result = await use_case.execute(
                        user_id=user_id,
                        room_id=room_id,
                        card_id=data["card_id"],
                    )

                    # 룸 전체에 브로드캐스트
                    await connection_manager.broadcast_to_room(
                        message={
                            "type": "new_message",
                            "message": {
                                "message_id": result.message_id,
                                "user_id": result.user_id,
                                "content": result.content,
                                "card_id": result.card_id,
                                "message_type": result.message_type,
                                "created_at": result.created_at.isoformat(),
                            },
                        },
                        room_id=room_id,
                    )
                except BeZeroError as e:
                    await websocket.send_json({"type": "error", "error": e.code.value})

            elif message_type == "get_history":
                # 메시지 히스토리 조회
                try:
                    use_case = GetMessageHistoryUseCase(chat_message_service, room_stay_service)
                    results = await use_case.execute(
                        user_id=user_id,
                        room_id=room_id,
                        cursor=data.get("cursor"),
                        limit=data.get("limit", 50),
                    )

                    await websocket.send_json(
                        {
                            "type": "history",
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
                            ],
                        }
                    )
                except BeZeroError as e:
                    await websocket.send_json({"type": "error", "error": e.code.value})

    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected from room {room_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        # 7. 연결 종료
        connection_manager.disconnect(room_id, user_id)

        # 8. 퇴장 시스템 메시지 전송
        try:
            system_message = await chat_message_service.create_system_message(
                room_id=Id.from_hex(room_id),
                content=MessageContent("사용자가 퇴장했습니다."),
            )
            await session.commit()

            await connection_manager.broadcast_to_room(
                message={
                    "type": "system_message",
                    "message": {
                        "message_id": system_message.message_id.to_hex(),
                        "content": system_message.content.value,
                        "created_at": system_message.created_at.isoformat(),
                    },
                },
                room_id=room_id,
            )
        except Exception as e:
            logger.error(f"Failed to send leave system message: {e}")


@router.get("/cities/{city_id}/conversation-cards/random")
async def get_random_conversation_card(
    city_id: str,
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
):
    """도시별 랜덤 대화 카드 조회 (REST API).

    Args:
        city_id: 도시 ID (hex 문자열)
        session: 데이터베이스 세션

    Returns:
        랜덤으로 선택된 대화 카드
    """
    conversation_card_service = ConversationCardService(
        conversation_card_repository=SqlAlchemyConversationCardRepository(session),
    )
    use_case = GetRandomCardUseCase(conversation_card_service)
    return await use_case.execute(city_id)
