"""Socket.IO 연결 및 해제 핸들러 (Lifecycle)"""
import logging
from typing import Any
from uuid import uuid4

from bzero.application.results import ChatMessageResult
from bzero.application.use_cases.chat_messages import CreateSystemMessageUseCase
from bzero.application.use_cases.room_stays import VerifyRoomAccessUseCase
from bzero.core.database import get_async_db_session
from bzero.core.settings import get_settings
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent, SystemMessage
from bzero.infrastructure.auth.jwt_utils import verify_supabase_jwt
from bzero.presentation.api.dependencies import (
    create_chat_message_service,
    create_room_stay_service,
)
from bzero.presentation.socketio.server import get_socketio_server
from bzero.presentation.socketio.utils import (
    emit_system_message,
    get_typed_session,
    handle_socketio_error,
)

logger = logging.getLogger(__name__)
sio = get_socketio_server()

# 데모용 상수 (demo.py와 동기화)
DEMO_ROOM_ID = "00000000-0000-0000-0000-000000000000"
DEMO_NAMESPACE = "/demo"


# --- Authenticated Namespace (/) ---

@sio.event
async def connect(sid: str, environ: dict, auth: dict | None):
    """클라이언트 연결 이벤트 (인증 필요)."""
    try:
        if not auth:
            raise ConnectionRefusedError("No auth data provided")

        token = auth.get("token")
        room_id = auth.get("room_id")

        if not token or not room_id:
            raise ConnectionRefusedError("Missing token or room_id")

        settings = get_settings()
        try:
            payload = verify_supabase_jwt(
                token=token,
                secret=settings.auth.supabase_jwt_secret.get_secret_value(),
                algorithm=settings.auth.jwt_algorithm,
            )
        except Exception:
            logger.info("JWT verification failed")
            raise ConnectionRefusedError("Invalid token")

        user_id = payload["sub"]

        # 룸 접근 권한 검증 (Use Case 사용)
        async with get_async_db_session() as session:
            room_stay_service = create_room_stay_service(session)
            await VerifyRoomAccessUseCase(room_stay_service).execute(user_id, room_id)

        # 세션 데이터 저장
        await sio.save_session(sid, {"user_id": user_id, "room_id": room_id})

        logger.info(f"User {user_id} authenticated (sid: {sid})")
        return True

    except ValueError as e:
        logger.warning(f"Connection refused: {e}")
        raise ConnectionRefusedError(str(e)) from e
    except Exception as e:
        logger.error(f"Connection error: {e}")
        raise ConnectionRefusedError("Internal server error") from e


@sio.event
async def disconnect(sid: str, reason: Any = None):
    """클라이언트 연결 해제 이벤트."""
    try:
        session = await get_typed_session(sio, sid, namespace="/")

        async with get_async_db_session() as db_session:
            chat_message_service = create_chat_message_service(db_session)
            use_case = CreateSystemMessageUseCase(db_session, chat_message_service)

            result = await use_case.execute(
                room_id=session.room_id,
                content=SystemMessage.USER_LEFT,
            )
            await emit_system_message(sio, session.room_id, result, namespace="/")

    except Exception as e:
        # 연결 해제 시의 에러는 로깅만 하고 무시 (이미 끊어진 상태일 수 있음)
        logger.debug(f"Error during disconnect: {e}")


# --- Demo Namespace (/demo) ---

@sio.on("connect", namespace=DEMO_NAMESPACE)
async def connect_demo(sid: str, environ: dict):
    """데모 연결 (인증 없음)."""
    try:
        user_id = str(uuid4())
        await sio.save_session(
            sid,
            {"user_id": user_id, "room_id": DEMO_ROOM_ID},
            namespace=DEMO_NAMESPACE,
        )

        await sio.emit(
            "connected",
            {"user_id": user_id},
            to=sid,
            namespace=DEMO_NAMESPACE,
        )

        logger.info(f"Demo user {user_id} connected (sid: {sid})")
        return True
    except Exception as e:
        logger.error(f"Demo connection error: {e}")
        return False


@sio.on("disconnect", namespace=DEMO_NAMESPACE)
async def disconnect_demo(sid: str, reason: Any = None):
    """데모 연결 해제."""
    try:
        session = await get_typed_session(sio, sid, namespace=DEMO_NAMESPACE)

        async with get_async_db_session() as db_session:
            chat_message_service = create_chat_message_service(db_session)
            system_message = await chat_message_service.create_system_message(
                room_id=Id.from_hex(DEMO_ROOM_ID),
                content=MessageContent(f"사용자 {session.user_id[:8]}... 님이 퇴장했습니다."),
            )

            await emit_system_message(
                sio,
                DEMO_ROOM_ID,
                ChatMessageResult.create_from(system_message),
                namespace=DEMO_NAMESPACE,
            )
            await db_session.commit()

        await sio.leave_room(sid, DEMO_ROOM_ID, namespace=DEMO_NAMESPACE)
        logger.info(f"Demo user {session.user_id} disconnected")

    except Exception as e:
        logger.debug(f"Error during demo disconnect: {e}")
