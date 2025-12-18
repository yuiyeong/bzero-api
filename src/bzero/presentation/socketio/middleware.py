"""Socket.IO 미들웨어"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.core.settings import get_settings
from bzero.domain.errors import BeZeroError
from bzero.domain.services import RoomStayService
from bzero.domain.value_objects import Id
from bzero.infrastructure.auth.jwt_utils import verify_supabase_jwt
from bzero.infrastructure.repositories.room_stay import SqlAlchemyRoomStayRepository

logger = logging.getLogger(__name__)


async def verify_jwt_token(token: str) -> dict:
    """JWT 토큰을 검증합니다.

    Args:
        token: JWT 토큰

    Returns:
        JWT 페이로드 (sub, email 등)

    Raises:
        ValueError: 토큰 검증 실패 시
    """
    settings = get_settings()

    try:
        payload = verify_supabase_jwt(
            token=token,
            secret=settings.auth.supabase_jwt_secret.get_secret_value(),
            audience=settings.auth.supabase_jwt_audience,
        )
        return payload
    except Exception as e:
        logger.error(f"JWT verification failed: {e}")
        raise ValueError(f"Invalid token: {e}") from e


async def verify_room_access(user_id: str, room_id: str, session: AsyncSession) -> None:
    """사용자가 해당 룸에 접근 권한이 있는지 검증합니다.

    Args:
        user_id: 사용자 ID (hex)
        room_id: 룸 ID (hex)
        session: DB 세션

    Raises:
        ValueError: 접근 권한이 없는 경우
    """
    room_stay_service = RoomStayService(
        room_stay_repository=SqlAlchemyRoomStayRepository(session),
    )

    try:
        await room_stay_service.get_stays_by_user_id_and_room_id(
            user_id=Id.from_hex(user_id),
            room_id=Id.from_hex(room_id),
        )
    except BeZeroError as e:
        raise ValueError(f"Access denied: {e.code.value}") from e
