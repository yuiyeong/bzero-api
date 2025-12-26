"""Socket.IO 채팅 핸들러 (인증 필요)"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.use_cases.chat_messages import (
    CreateSystemMessageUseCase,
    SendMessageUseCase,
    ShareCardUseCase,
)
from bzero.application.use_cases.room_stays import VerifyRoomAccessUseCase
from bzero.domain.value_objects.chat_message import SystemMessage
from bzero.presentation.api.dependencies import (
    create_chat_message_service,
    create_conversation_card_service,
    create_room_stay_service,
    create_user_service,
)
from bzero.presentation.schemas.chat_message import (
    SendMessageRequest,
    ShareCardRequest,
)
from bzero.presentation.schemas.socketio import JoinRoomRequest
from bzero.presentation.socketio.dependencies import socket_handler
from bzero.presentation.socketio.server import get_socketio_server
from bzero.presentation.socketio.utils import (
    emit_new_message,
    emit_system_message,
    get_typed_session,
)


logger = logging.getLogger(__name__)
sio = get_socketio_server()


@sio.on("join_room")
@socket_handler(schema=JoinRoomRequest)
async def handle_join_room(sid: str, request: JoinRoomRequest, db_session: AsyncSession):
    """클라이언트가 룸에 참여하는 이벤트."""
    session = await get_typed_session(sio, sid)

    if request.room_id != session.room_id:
        raise ValueError("Room ID mismatch")

    # 1. 룸 접근 권한 검증
    room_stay_service = create_room_stay_service(db_session)
    await VerifyRoomAccessUseCase(room_stay_service).execute(session.user_id, session.room_id)

    # 2. Socket.IO 룸 입장
    await sio.enter_room(sid, session.room_id)

    # 3. 입장 시스템 메시지 생성 및 브로드캐스트
    chat_message_service = create_chat_message_service(db_session)
    use_case = CreateSystemMessageUseCase(db_session, chat_message_service)
    result = await use_case.execute(
        room_id=session.room_id,
        content=SystemMessage.USER_JOINED,
    )
    await emit_system_message(sio, session.room_id, result)


@sio.on("send_message")
@socket_handler(schema=SendMessageRequest)
async def handle_send_message(sid: str, request: SendMessageRequest, db_session: AsyncSession):
    """텍스트 메시지 전송 이벤트."""
    session = await get_typed_session(sio, sid)

    chat_message_service = create_chat_message_service(db_session)
    user_service = create_user_service(db_session)
    use_case = SendMessageUseCase(db_session, chat_message_service, user_service)

    result = await use_case.execute(
        room_id=session.room_id,
        content=request.content,
        user_id=session.user_id,
    )
    await emit_new_message(sio, session.room_id, result)


# get_history 핸들러 제거됨 (REST API GET /api/v1/rooms/{room_id}/messages 로 마이그레이션)


@sio.on("share_card")
@socket_handler(schema=ShareCardRequest)
async def handle_share_card(sid: str, request: ShareCardRequest, db_session: AsyncSession):
    """카드 공유 이벤트."""
    session = await get_typed_session(sio, sid)

    chat_message_service = create_chat_message_service(db_session)
    conversation_card_service = create_conversation_card_service(db_session)
    user_service = create_user_service(db_session)
    use_case = ShareCardUseCase(db_session, chat_message_service, conversation_card_service, user_service)

    result = await use_case.execute(
        room_id=session.room_id,
        card_id=request.card_id,
        user_id=session.user_id,
    )
    await emit_new_message(sio, session.room_id, result)
