"""대화 거절 유스케이스.

대화 수신자(user2)가 신청을 거절합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.dm import DirectMessageRoomResult
from bzero.domain.services.direct_message_room import DirectMessageRoomService
from bzero.domain.value_objects import Id


class RejectDMRequestUseCase:
    """대화 거절 유스케이스.

    user2(수신자)가 대화 신청을 거절합니다.
    PENDING 상태인 대화방만 거절할 수 있습니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        dm_room_service: DirectMessageRoomService,
    ):
        """RejectDMRequestUseCase를 초기화합니다.

        Args:
            session: 데이터베이스 세션
            dm_room_service: 대화방 도메인 서비스
        """
        self._session = session
        self._dm_room_service = dm_room_service

    async def execute(
        self,
        dm_room_id: str,
        user_id: str,
    ) -> DirectMessageRoomResult:
        """대화 거절을 실행합니다.

        Args:
            dm_room_id: 대화방 ID (hex 문자열)
            user_id: 거절하는 사용자 ID (hex 문자열)

        Returns:
            업데이트된 대화방 정보 (status: REJECTED)

        Raises:
            NotFoundDMRoomError: 대화방을 찾을 수 없는 경우
            ForbiddenDMRoomAccessError: 거절 권한이 없는 경우
            InvalidDMRoomStatusError: PENDING 상태가 아닌 경우
        """
        # 1. 대화 거절 (도메인 서비스)
        dm_room = await self._dm_room_service.reject_dm_request(
            dm_room_id=Id.from_hex(dm_room_id),
            user_id=Id.from_hex(user_id),
        )

        # 2. 트랜잭션 커밋
        await self._session.commit()

        return DirectMessageRoomResult.create_from(dm_room)
