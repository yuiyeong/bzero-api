"""대화 카드 공유 유스케이스.

사용자가 룸에 대화 카드를 공유하는 비즈니스 로직을 담당합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results import ChatMessageResult
from bzero.domain.errors import UnauthorizedError
from bzero.domain.services import ChatMessageService, ConversationCardService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import AuthProvider, Id


class ShareCardUseCase:
    """대화 카드 공유 유스케이스.

    사용자가 선택한 대화 카드를 룸에 공유합니다.
    Rate Limiting(2초에 1회)을 통해 스팸을 방지합니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        chat_message_service: ChatMessageService,
        conversation_card_service: ConversationCardService,
        user_service: UserService,
    ):
        """ShareCardUseCase를 초기화합니다.

        Args:
            session: 데이터베이스 세션
            chat_message_service: 채팅 메시지 도메인 서비스
            conversation_card_service: 대화 카드 도메인 서비스
        """
        self._session = session
        self._chat_message_service = chat_message_service
        self._conversation_card_service = conversation_card_service
        self._user_service = user_service

    async def execute(
        self,
        room_id: str,
        card_id: str,
        user_id: str | None = None,
        provider: str | None = None,
        provider_user_id: str | None = None,
    ) -> ChatMessageResult:
        """대화 카드 공유를 실행합니다.

        Args:
            user_id: 카드 공유자 ID (hex 문자열)
            room_id: 카드를 공유할 룸 ID (hex 문자열)
            card_id: 공유할 대화 카드 ID (hex 문자열)

        Returns:
            생성된 메시지 정보 (CARD_SHARED 타입)

        Raises:
            RateLimitExceededError: 2초 이내 중복 요청 시
            NotFoundConversationCardError: 카드를 찾을 수 없는 경우
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

        # 2. 대화 카드 조회
        card = await self._conversation_card_service.get_card_by_id(Id.from_hex(card_id))

        # 2. 카드 공유 메시지 생성 (Rate Limiting 적용)
        message = await self._chat_message_service.share_conversation_card(
            user_id=Id.from_hex(user_id),
            room_id=Id.from_hex(room_id),
            card_id=card.card_id,
            card_question=card.question,
        )

        # 3. 트랜잭션 커밋
        await self._session.commit()

        return ChatMessageResult.create_from(message)
