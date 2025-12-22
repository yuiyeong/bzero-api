import functools
import logging
from typing import Any, Callable, Type, TypeVar

from pydantic import BaseModel, ValidationError

from bzero.core.database import get_async_db_session
from bzero.presentation.socketio.server import get_socketio_server
from bzero.presentation.socketio.utils import handle_socketio_error

logger = logging.getLogger(__name__)
sio = get_socketio_server()

T = TypeVar("T", bound=BaseModel)


def socket_handler(schema: Type[T] | None = None, namespace: str = "/"):
    """Socket.IO 핸들러를 위한 데코레이터.

    - DB 세션을 자동으로 생성하고 핸들러에 주입합니다.
    - 입력을 지정된 Pydantic 스키마로 검증하고 변환합니다.
    - 발생하는 예외를 handle_socketio_error로 통합 처리합니다.

    Args:
        schema: 입력 데이터 검증을 위한 Pydantic 모델 클래스
        namespace: 소켓 네임스페이스
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(sid: str, *args, **kwargs):
            try:
                # 1. 데이터 검증 (args[0]이 보통 클라이언트가 보낸 데이터)
                validated_data = None
                if schema:
                    if not args:
                        raise ValueError("No data received for validation")
                    data = args[0]
                    try:
                        validated_data = schema.model_validate(data)
                    except ValidationError as e:
                        logger.warning(f"Validation failed for {func.__name__}: {e}")
                        await handle_socketio_error(sio, sid, e, namespace=namespace)
                        return

                # 2. DB 세션 주입 및 핸들러 호출
                async with get_async_db_session() as session:
                    if validated_data:
                        return await func(sid, validated_data, session, *args[1:], **kwargs)
                    else:
                        return await func(sid, session, *args, **kwargs)

            except Exception as e:
                await handle_socketio_error(sio, sid, e, namespace=namespace)

        return wrapper

    return decorator
