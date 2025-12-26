"""대화 수락 유스케이스.

대화 수신자(user2)가 신청을 수락합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.dm import DirectMessageRoomResult
from bzero.domain.services.direct_message_room import DirectMessageRoomService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import AuthProvider, Id


class AcceptDMRequestUseCase:
    """대화 수락 유스케이스.

    user2(수신자)가 대화 신청을 수락합니다.
    PENDING 상태인 대화방만 수락할 수 있습니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        dm_room_service: DirectMessageRoomService,
        user_service: UserService,
    ):
        """AcceptDMRequestUseCase를 초기화합니다.

        Args:
            session: 데이터베이스 세션
            dm_room_service: 대화방 도메인 서비스
            user_service: 사용자 도메인 서비스
        """
        self._session = session
        self._dm_room_service = dm_room_service
        self._user_service = user_service

    async def execute(
        self,
        dm_room_id: str,
        provider: str,
        provider_user_id: str,
    ) -> DirectMessageRoomResult:
        """대화 신청 수락을 실행합니다.

        Args:
            dm_room_id: 대화방 ID
            provider: 인증 제공자
            provider_user_id: 인증 제공자의 사용자 ID

        Returns:
            업데이트된 대화방 정보

        Raises:
            UnauthorizedError: 사용자를 찾을 수 없는 경우
            NotFoundDMRoomError: 대화방을 찾을 수 없는 경우
            ForbiddenDMRoomAccessError: 수락 권한이 없는 경우
            InvalidDMRoomStatusError: PENDING 상태가 아닌 경우
        """
        # 1. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )
        user_id = user.user_id.value.hex
        # 1. 대화 수락 (도메인 서비스)
        dm_room = await self._dm_room_service.accept_dm_request(
            dm_room_id=Id.from_hex(dm_room_id),
            user_id=Id.from_hex(user_id),
        )

        # 2. 트랜잭션 커밋
        await self._session.commit()

        return DirectMessageRoomResult.create_from(dm_room)
