"""Socket.IO 1:1 대화(DM) 핸들러 (인증 필요)"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.use_cases.dm import GetDMHistoryUseCase, SendDMMessageUseCase
from bzero.presentation.api.dependencies import (
    create_dm_room_service,
    create_dm_service,
)
from bzero.presentation.schemas.dm import (
    DirectMessageResponse,
    JoinDMRoomRequest,
    SendDMMessageRequest,
)
from bzero.presentation.socketio.dependencies import socket_handler
from bzero.presentation.socketio.server import get_socketio_server
from bzero.presentation.socketio.utils import get_typed_session


logger = logging.getLogger(__name__)
sio = get_socketio_server()


async def emit_new_dm_message(
    dm_room_id: str,
    result: "DirectMessageResponse",
    namespace: str = "/",
) -> None:
    """새 DM 메시지를 대화방에 브로드캐스트합니다."""
    await sio.emit(
        "new_dm_message",
        {"message": result.model_dump(mode="json")},
        room=f"dm:{dm_room_id}",
        namespace=namespace,
    )


async def emit_dm_request_notification(
    to_user_sid: str,
    dm_room_id: str,
    from_user_id: str,
    namespace: str = "/",
) -> None:
    """대화 신청 알림을 특정 사용자에게 전송합니다.

    REST API에서 호출됩니다.
    """
    await sio.emit(
        "dm_request_notification",
        {
            "dm_room_id": dm_room_id,
            "from_user_id": from_user_id,
        },
        to=to_user_sid,
        namespace=namespace,
    )


async def emit_dm_status_changed(
    to_user_sid: str,
    dm_room_id: str,
    status: str,
    updated_by_user_id: str,
    namespace: str = "/",
) -> None:
    """대화 상태 변경 알림을 특정 사용자에게 전송합니다.

    REST API에서 호출됩니다 (수락/거절 시).
    """
    await sio.emit(
        "dm_status_changed",
        {
            "dm_room_id": dm_room_id,
            "status": status,
            "updated_by": updated_by_user_id,
        },
        to=to_user_sid,
        namespace=namespace,
    )


@sio.on("join_dm_room")
@socket_handler(schema=JoinDMRoomRequest)
async def handle_join_dm_room(sid: str, request: JoinDMRoomRequest, db_session: AsyncSession):
    """클라이언트가 1:1 대화방에 참여하는 이벤트.

    대화방 참여자 검증 후 Socket.IO 룸에 입장합니다.
    입장 시 읽지 않은 메시지를 읽음 처리합니다.
    """
    session = await get_typed_session(sio, sid)

    # 1. 대화방 접근 권한 검증 및 읽음 처리
    dm_room_service = create_dm_room_service(db_session)
    dm_service = create_dm_service(db_session)
    use_case = GetDMHistoryUseCase(db_session, dm_room_service, dm_service)

    # 접근 권한 검증만 수행 (메시지 조회 없이)
    await use_case.execute(
        dm_room_id=request.dm_room_id,
        user_id=session.user_id,
        limit=1,
        mark_as_read=True,
    )

    # 2. Socket.IO 룸 입장 (dm: prefix로 구분)
    dm_room_key = f"dm:{request.dm_room_id}"
    await sio.enter_room(sid, dm_room_key)

    logger.info(f"User {session.user_id} joined DM room {request.dm_room_id}")


@sio.on("send_dm_message")
@socket_handler(schema=SendDMMessageRequest)
async def handle_send_dm_message(sid: str, request: SendDMMessageRequest, db_session: AsyncSession):
    """1:1 메시지 전송 이벤트.

    Rate Limiting(2초에 1회)이 적용됩니다.
    첫 메시지 전송 시 ACCEPTED → ACTIVE로 상태가 전환됩니다.
    """
    session = await get_typed_session(sio, sid)

    # 1. 메시지 전송
    dm_room_service = create_dm_room_service(db_session)
    dm_service = create_dm_service(db_session)
    use_case = SendDMMessageUseCase(db_session, dm_room_service, dm_service)

    result = await use_case.execute(
        dm_room_id=request.dm_room_id,
        user_id=session.user_id,
        content=request.content,
    )

    # 2. 대화방에 브로드캐스트
    response = DirectMessageResponse.create_from(result)
    await emit_new_dm_message(request.dm_room_id, response)
