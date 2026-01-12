"""시스템 메시지 생성 유스케이스.

입장/퇴장/공지 등의 시스템 메시지를 생성하는 비즈니스 로직을 담당합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results import ChatMessageResult
from bzero.domain.services import ChatMessageService
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent


class CreateSystemMessageUseCase:
    """시스템 메시지 생성 유스케이스.

    룸에 시스템 메시지를 생성합니다 (예: 입장/퇴장 알림).
    시스템 메시지는 Rate Limiting을 적용하지 않습니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        chat_message_service: ChatMessageService,
    ):
        """CreateSystemMessageUseCase를 초기화합니다.

        Args:
            session: 데이터베이스 세션
            chat_message_service: 채팅 메시지 도메인 서비스
        """
        self._session = session
        self._chat_message_service = chat_message_service

    async def execute(
        self,
        room_id: str,
        content: str,
        roomstays_id: str | None = None,
    ) -> tuple[ChatMessageResult, bool]:
        """시스템 메시지 생성을 실행합니다.

        Args:
            room_id: 메시지를 전송할 룸 ID (hex 문자열)
            content: 시스템 메시지 내용
            roomstays_id: 체류 ID (중복 체크용, optional hex string)

        Returns:
            (생성된 시스템 메시지 정보, 생성 여부) 튜플

        Raises:
            InvalidMessageContentError: 메시지 내용이 1-300자가 아닌 경우
        """
        # 1. 시스템 메시지 생성
        message, is_created = await self._chat_message_service.create_system_message(
            room_id=Id.from_hex(room_id),
            content=MessageContent(content),
            roomstays_id=Id.from_hex(roomstays_id) if roomstays_id else None,
        )

        # 2. 트랜잭션 커밋
        await self._session.commit()

        return ChatMessageResult.create_from(message), is_created
