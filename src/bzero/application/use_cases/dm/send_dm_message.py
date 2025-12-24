"""메시지 전송 유스케이스.

사용자가 1:1 대화방에 메시지를 전송합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.dm import DirectMessageResult
from bzero.domain.services.direct_message import DirectMessageService
from bzero.domain.services.direct_message_room import DirectMessageRoomService
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent


class SendDMMessageUseCase:
    """메시지 전송 유스케이스.

    사용자가 1:1 대화방에 메시지를 전송합니다.
    Rate Limiting(2초에 1회)을 통해 스팸을 방지합니다.
    첫 메시지 전송 시 ACCEPTED → ACTIVE로 상태가 전환됩니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        dm_room_service: DirectMessageRoomService,
        dm_service: DirectMessageService,
    ):
        """SendDMMessageUseCase를 초기화합니다.

        Args:
            session: 데이터베이스 세션
            dm_room_service: 대화방 도메인 서비스
            dm_service: 메시지 도메인 서비스
        """
        self._session = session
        self._dm_room_service = dm_room_service
        self._dm_service = dm_service

    async def execute(
        self,
        dm_room_id: str,
        user_id: str,
        content: str,
    ) -> DirectMessageResult:
        """메시지 전송을 실행합니다.

        Args:
            dm_room_id: 대화방 ID (hex 문자열)
            user_id: 메시지 전송자 ID (hex 문자열)
            content: 메시지 내용 (1-300자)

        Returns:
            생성된 메시지 정보

        Raises:
            NotFoundDMRoomError: 대화방을 찾을 수 없는 경우
            ForbiddenDMRoomAccessError: 참여자가 아닌 경우
            InvalidDMRoomStatusError: 메시지 전송 불가 상태인 경우
            RateLimitExceededError: 2초 이내 중복 요청 시
            InvalidMessageContentError: 메시지 내용이 1-300자가 아닌 경우
        """
        # 1. 대화방 조회
        dm_room = await self._dm_room_service.get_dm_room_by_id(Id.from_hex(dm_room_id))

        # 2. 메시지 전송 (Rate Limiting, 상태 전환 포함)
        message, _ = await self._dm_service.send_message(
            dm_room=dm_room,
            from_user_id=Id.from_hex(user_id),
            content=MessageContent(content),
        )

        # 3. 트랜잭션 커밋
        await self._session.commit()

        return DirectMessageResult.create_from(message)
