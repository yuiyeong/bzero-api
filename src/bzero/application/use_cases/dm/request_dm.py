"""대화 신청 유스케이스.

사용자가 같은 룸에 체류 중인 다른 사용자에게 1:1 대화를 신청합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.dm import DirectMessageRoomResult
from bzero.domain.services.direct_message_room import DirectMessageRoomService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import AuthProvider, Id


class RequestDMUseCase:
    """대화 신청 유스케이스.

    같은 룸에 체류 중인 사용자에게 1:1 대화를 신청합니다.
    중복 신청은 불가합니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        dm_room_service: DirectMessageRoomService,
        user_service: UserService,
    ):
        """RequestDMUseCase를 초기화합니다.

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
        provider: str,
        provider_user_id: str,
        target_id: str,
    ) -> DirectMessageRoomResult:
        """1:1 대화 신청을 실행합니다.

        Args:
            provider: 인증 제공자
            provider_user_id: 인증 제공자의 사용자 ID
            target_id: 대화 상대방 ID (user_id)

        Returns:
            생성된 대화방 정보

        Raises:
            UnauthorizedError: 사용자를 찾을 수 없는 경우
            NotInSameRoomError: 같은 룸에 체류 중이 아닌 경우
            DuplicatedDMRequestError: 이미 활성 대화방이 존재하는 경우
        """
        # 1. 요청자 조회
        requester = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )
        requester_id = requester.user_id.value.hex
        # 1. 대화 신청 (도메인 서비스)
        dm_room = await self._dm_room_service.request_dm(
            requester_id=Id.from_hex(requester_id),
            target_id=Id.from_hex(target_id),
        )

        # 2. 트랜잭션 커밋
        await self._session.commit()

        return DirectMessageRoomResult.create_from(dm_room)
