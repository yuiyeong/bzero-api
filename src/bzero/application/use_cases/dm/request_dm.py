"""대화 신청 유스케이스.

사용자가 같은 룸에 체류 중인 다른 사용자에게 1:1 대화를 신청합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.dm import DirectMessageRoomResult
from bzero.domain.services.direct_message_room import DirectMessageRoomService
from bzero.domain.value_objects import Id


class RequestDMUseCase:
    """대화 신청 유스케이스.

    같은 룸에 체류 중인 사용자에게 1:1 대화를 신청합니다.
    중복 신청은 불가합니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        dm_room_service: DirectMessageRoomService,
    ):
        """RequestDMUseCase를 초기화합니다.

        Args:
            session: 데이터베이스 세션
            dm_room_service: 대화방 도메인 서비스
        """
        self._session = session
        self._dm_room_service = dm_room_service

    async def execute(
        self,
        requester_id: str,
        target_id: str,
    ) -> DirectMessageRoomResult:
        """대화 신청을 실행합니다.

        Args:
            requester_id: 대화 신청자 ID (hex 문자열)
            target_id: 대화 수신자 ID (hex 문자열)

        Returns:
            생성된 대화방 정보 (status: PENDING)

        Raises:
            NotInSameRoomError: 같은 룸에 체류 중이 아닌 경우
            DuplicatedDMRequestError: 이미 활성 대화방이 존재하는 경우
        """
        # 1. 대화 신청 (도메인 서비스)
        dm_room = await self._dm_room_service.request_dm(
            requester_id=Id.from_hex(requester_id),
            target_id=Id.from_hex(target_id),
        )

        # 2. 트랜잭션 커밋
        await self._session.commit()

        return DirectMessageRoomResult.create_from(dm_room)
