"""Socket.IO 채팅 핸들러 (인증 필요)"""
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.use_cases.chat_messages import (
    CreateSystemMessageUseCase,
    GetMessageHistoryUseCase,
    SendMessageUseCase,
    ShareCardUseCase,
)
from bzero.application.use_cases.room_stays import VerifyRoomAccessUseCase
from bzero.core.database import get_async_db_session
from bzero.presentation.api.dependencies import (
    create_chat_message_service,
    create_conversation_card_service,
    create_room_stay_service,
)
from bzero.domain.value_objects.chat_message import SystemMessage
from bzero.presentation.socketio.dependencies import socket_handler
from bzero.presentation.schemas.chat_message import (
    GetHistoryRequest,
    SendMessageRequest,
    ShareCardRequest,
)
from bzero.presentation.schemas.socketio import JoinRoomRequest
from bzero.presentation.socketio.server import get_socketio_server
from bzero.presentation.socketio.utils import (
    emit_new_message,
    emit_system_message,
    get_typed_session,
    handle_socketio_error,
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
    use_case = SendMessageUseCase(db_session, chat_message_service)

    result = await use_case.execute(session.user_id, session.room_id, request.content)
    await emit_new_message(sio, session.room_id, result)


@sio.on("share_card")
@socket_handler(schema=ShareCardRequest)
async def handle_share_card(sid: str, request: ShareCardRequest, db_session: AsyncSession):
    """카드 공유 이벤트."""
    session = await get_typed_session(sio, sid)

    chat_message_service = create_chat_message_service(db_session)
    conversation_card_service = create_conversation_card_service(db_session)
    use_case = ShareCardUseCase(db_session, chat_message_service, conversation_card_service)

    result = await use_case.execute(session.user_id, session.room_id, request.card_id)
    await emit_new_message(sio, session.room_id, result)


@sio.on("get_history")
@socket_handler(schema=GetHistoryRequest)
async def handle_get_history(sid: str, request: GetHistoryRequest, db_session: AsyncSession):
    """메시지 히스토리 조회 이벤트."""
    session = await get_typed_session(sio, sid)

    chat_message_service = create_chat_message_service(db_session)
    room_stay_service = create_room_stay_service(db_session)
    use_case = GetMessageHistoryUseCase(chat_message_service, room_stay_service)

    results = await use_case.execute(
        session.user_id, session.room_id, request.cursor, request.limit
    )

    # 요청한 클라이언트에게만 응답
    await sio.emit(
        "history",
        {"messages": [msg.to_dict() for msg in results]},
        to=sid,
    )
