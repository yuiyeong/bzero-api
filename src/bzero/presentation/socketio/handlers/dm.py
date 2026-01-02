"""Socket.IO 1:1 대화(DM) 핸들러 (인증 필요)"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.use_cases.dm import GetDMHistoryUseCase, SendDMMessageUseCase
from bzero.core.database import get_async_db_session_ctx
from bzero.core.settings import get_settings
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import AuthProvider
from bzero.infrastructure.auth.jwt_utils import verify_supabase_jwt
from bzero.infrastructure.repositories.user import SqlAlchemyUserRepository
from bzero.infrastructure.repositories.user_identity import SqlAlchemyUserIdentityRepository
from bzero.presentation.api.dependencies import (
    create_dm_room_service,
    create_dm_service,
    create_user_service,
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
DM_NAMESPACE = "/dm"


@sio.event(namespace=DM_NAMESPACE)
async def connect(sid: str, environ: dict, auth: dict | None):
    """클라이언트 연결 이벤트 (인증 필요)."""
    try:
        if not auth:
            raise ConnectionRefusedError("No auth data provided")

        token = auth.get("token")
        dm_room_id = auth.get("dm_room_id")

        if not token or not dm_room_id:
            raise ConnectionRefusedError("Missing token or dm_room_id")

        settings = get_settings()
        try:
            payload = verify_supabase_jwt(
                token=token,
                secret=settings.auth.supabase_jwt_secret.get_secret_value(),
                algorithm=settings.auth.jwt_algorithm,
            )
        except Exception:
            logger.info("JWT verification failed")
            raise ConnectionRefusedError("Invalid token") from None

        async with get_async_db_session_ctx() as session:
            # 1. 사용자 조회
            user_repository = SqlAlchemyUserRepository(session)
            user_identity_repository = SqlAlchemyUserIdentityRepository(session)
            user_service = UserService(user_repository, user_identity_repository, settings.timezone)

            try:
                provider = payload.get("app_metadata", {}).get("provider")
                provider_user_id = payload.get("sub")
                user = await user_service.find_user_by_provider_and_provider_user_id(
                    provider=AuthProvider(provider),
                    provider_user_id=provider_user_id,
                )
                user_id = user.user_id.value.hex
            except Exception:
                raise ConnectionRefusedError("User not found") from None

            # 2. DM Room 접근 권한 검증 (간단히 참여자인지 확인)
            # GetDMHistoryUseCase를 활용 (limit=0 or verify logic only)
            # 여기서는 직접 Service를 써도 되지만 UseCase 재활용
            dm_room_service = create_dm_room_service(session)
            dm_service = create_dm_service(session)

            # UseCase 호출하여 검증
            use_case = GetDMHistoryUseCase(session, dm_room_service, dm_service, user_service)
            # limit=0이어도 검증 로직은 수행됨
            await use_case.execute(
                dm_room_id=dm_room_id,
                user_id=user_id,
                limit=1,
                mark_as_read=False,  # 연결 시 읽음 처리는 join_dm_room 혹은 별도 로직에서?
            )

        # 세션 데이터 저장
        # SocketSession 스키마(room_id 필수)를 만족하기 위해 dm_room_id를 room_id로 저장
        await sio.save_session(sid, {"user_id": user_id, "room_id": dm_room_id}, namespace=DM_NAMESPACE)

        # DM 방 Room 입장 (SocketIO room)
        # 중요: 클라이언트는 연결 후 자동 입장 원함?
        # join_dm_room 이벤트가 별도로 있으므로 거기서 처리해도 됨.
        # 하지만 연결되면 바로 방에 들어가는 게 자연스러움.
        # use-dm-socket.ts는 connect 후 join_dm_room을 emit함.
        # 중복 입장은 문제 없음.

        logger.info(f"User {user_id} connected to DM Namespace (sid: {sid})")
        return True

    except Exception as e:
        logger.warning(f"DM Connection refused: {e}")
        raise ConnectionRefusedError(str(e)) from e


async def emit_new_dm_message(
    dm_room_id: str,
    result: "DirectMessageResponse",
    namespace: str = DM_NAMESPACE,
) -> None:
    """새 DM 메시지를 대화방에 브로드캐스트합니다."""
    await sio.emit(
        "new_dm_message",
        {"message": result.model_dump(mode="json")},
        room=f"dm:{dm_room_id}",
        namespace=namespace,
    )


async def emit_dm_request_notification(
    to_user_id: str,
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
        to=f"user:{to_user_id}",
        namespace=namespace,
    )


async def emit_dm_status_changed(
    to_user_id: str,
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
        to=f"user:{to_user_id}",
        namespace=namespace,
    )


@sio.on("join_dm_room", namespace=DM_NAMESPACE)
@socket_handler(schema=JoinDMRoomRequest)
async def handle_join_dm_room(sid: str, request: JoinDMRoomRequest, db_session: AsyncSession):
    """클라이언트가 1:1 대화방에 참여하는 이벤트.

    대화방 참여자 검증 후 Socket.IO 룸에 입장합니다.
    입장 시 읽지 않은 메시지를 읽음 처리합니다.
    """
    session = await get_typed_session(sio, sid, namespace=DM_NAMESPACE)

    # 1. 대화방 접근 권한 검증 및 읽음 처리
    dm_room_service = create_dm_room_service(db_session)
    dm_service = create_dm_service(db_session)
    user_service = create_user_service(db_session)
    use_case = GetDMHistoryUseCase(db_session, dm_room_service, dm_service, user_service)

    # 접근 권한 검증만 수행 (메시지 조회 없이)
    await use_case.execute(
        dm_room_id=request.dm_room_id,
        user_id=session.user_id,
        limit=1,
        mark_as_read=True,
    )

    # 2. Socket.IO 룸 입장 (dm: prefix로 구분)
    dm_room_key = f"dm:{request.dm_room_id}"
    await sio.enter_room(sid, dm_room_key, namespace=DM_NAMESPACE)

    logger.info(f"User {session.user_id} joined DM room {request.dm_room_id}")


@sio.on("send_dm_message", namespace=DM_NAMESPACE)
@socket_handler(schema=SendDMMessageRequest)
async def handle_send_dm_message(sid: str, request: SendDMMessageRequest, db_session: AsyncSession):
    """1:1 메시지 전송 이벤트.

    Rate Limiting(2초에 1회)이 적용됩니다.
    첫 메시지 전송 시 ACCEPTED → ACTIVE로 상태가 전환됩니다.
    """
    session = await get_typed_session(sio, sid, namespace=DM_NAMESPACE)

    # 1. 메시지 전송
    dm_room_service = create_dm_room_service(db_session)
    dm_service = create_dm_service(db_session)
    user_service = create_user_service(db_session)
    use_case = SendDMMessageUseCase(db_session, dm_room_service, dm_service, user_service)

    result = await use_case.execute(
        dm_room_id=request.dm_room_id,
        user_id=session.user_id,
        content=request.content,
    )

    # 2. 대화방에 브로드캐스트
    response = DirectMessageResponse.create_from(result)
    await emit_new_dm_message(request.dm_room_id, response)
