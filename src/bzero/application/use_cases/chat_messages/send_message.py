"""메시지 전송 유스케이스.

사용자가 룸에 텍스트 메시지를 전송하는 비즈니스 로직을 담당합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results import ChatMessageResult
from bzero.domain.services import ChatMessageService
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent


class SendMessageUseCase:
    """메시지 전송 유스케이스.

    사용자가 룸에 텍스트 메시지를 전송합니다.
    Rate Limiting(2초에 1회)을 통해 스팸을 방지합니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        chat_message_service: ChatMessageService,
    ):
        """SendMessageUseCase를 초기화합니다.

        Args:
            session: 데이터베이스 세션
            chat_message_service: 채팅 메시지 도메인 서비스
        """
        self._session = session
        self._chat_message_service = chat_message_service

    async def execute(
        self,
        user_id: str,
        room_id: str,
        content: str,
    ) -> ChatMessageResult:
        """메시지 전송을 실행합니다.

        Args:
            user_id: 메시지 전송자 ID (hex 문자열)
            room_id: 메시지를 전송할 룸 ID (hex 문자열)
            content: 메시지 내용 (1-300자)

        Returns:
            생성된 메시지 정보

        Raises:
            RateLimitExceededError: 2초 이내 중복 요청 시
            InvalidMessageContentError: 메시지 내용이 1-300자가 아닌 경우
        """
        # 1. 메시지 전송 (Rate Limiting 적용)
        message = await self._chat_message_service.send_message(
            user_id=Id.from_hex(user_id),
            room_id=Id.from_hex(room_id),
            content=MessageContent(content),
        )

        # 2. 트랜잭션 커밋
        await self._session.commit()

        return ChatMessageResult.create_from(message)
