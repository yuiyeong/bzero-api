"""메시지 전송 유스케이스.

사용자가 1:1 대화방에 메시지를 전송합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.dm import DirectMessageResult
from bzero.domain.errors import UnauthorizedError
from bzero.domain.services.direct_message import DirectMessageService
from bzero.domain.services.direct_message_room import DirectMessageRoomService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import AuthProvider, Id
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
        user_service: UserService,
    ):
        """SendDMMessageUseCase를 초기화합니다.

        Args:
            session: 데이터베이스 세션
            dm_room_service: 대화방 도메인 서비스
            dm_service: 메시지 도메인 서비스
            user_service: 사용자 도메인 서비스
        """
        self._session = session
        self._dm_room_service = dm_room_service
        self._dm_service = dm_service
        self._user_service = user_service

    async def execute(
        self,
        dm_room_id: str,
        content: str,
        user_id: str | None = None,
        provider: str | None = None,
        provider_user_id: str | None = None,
    ) -> DirectMessageResult:
        """메시지 전송을 실행합니다.

        Args:
            dm_room_id: 대화방 ID
            content: 메시지 내용
            user_id: 사용자 ID (Internal). provider 정보가 없을 경우 필수.
            provider: 인증 제공자. user_id가 없을 경우 필수.
            provider_user_id: 인증 제공자의 사용자 ID. user_id가 없을 경우 필수.

        Returns:
            생성된 메시지 정보

        Raises:
            UnauthorizedError: 사용자 식별 정보가 부족하거나 잘못된 경우
            NotFoundDMRoomError: 대화방을 찾을 수 없는 경우
            ForbiddenDMRoomAccessError: 참여자가 아닌 경우
            InvalidDMRoomStatusError: 메시지 전송 불가 상태인 경우
            RateLimitExceededError: 2초 이내 중복 요청 시
            InvalidMessageContentError: 메시지 내용이 1-300자가 아닌 경우
        """
        # 1. 사용자 식별
        if user_id is None:
            if provider is None or provider_user_id is None:
                raise UnauthorizedError("User identification required (user_id or provider info)")

            user = await self._user_service.find_user_by_provider_and_provider_user_id(
                provider=AuthProvider(provider),
                provider_user_id=provider_user_id,
            )
            user_id = user.user_id.value.hex

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
