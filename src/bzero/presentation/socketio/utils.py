"""Socket.IO 핸들러용 유틸리티"""
import logging
from contextlib import asynccontextmanager
from typing import Any

import socketio
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.core.database import get_async_db_session

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_db_session():
    """Socket.IO 핸들러용 DB 세션 컨텍스트 매니저.

    자동으로 commit/rollback을 처리합니다.

    사용 예:
        async with get_db_session() as session:
            # ... 비즈니스 로직 ...

    Yields:
        AsyncSession: 데이터베이스 세션
    """
    async for session in get_async_db_session():
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        break


async def get_session_data(
    sio: socketio.AsyncServer, sid: str, namespace: str = "/"
) -> dict[str, Any]:
    """세션 데이터를 조회하고 검증합니다.

    Args:
        sio: Socket.IO 서버 인스턴스
        sid: Session ID
        namespace: 네임스페이스 (기본값: "/")

    Returns:
        세션 데이터 (user_id, room_id 포함)

    Raises:
        ValueError: 세션 데이터가 없거나 유효하지 않은 경우
    """
    session_data = await sio.get_session(sid, namespace=namespace)

    if not session_data:
        raise ValueError("No session data")

    if "user_id" not in session_data or "room_id" not in session_data:
        raise ValueError("Invalid session data")

    return session_data
