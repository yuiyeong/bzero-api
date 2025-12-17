"""채팅 메시지 도메인 서비스 (비동기).

채팅 메시지의 전송, 조회, 카드 공유 등 핵심 비즈니스 로직을 처리합니다.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from bzero.domain.entities import ChatMessage
from bzero.domain.errors import NotFoundChatMessageError
from bzero.domain.ports.rate_limiter import RateLimiter
from bzero.domain.repositories.chat_message import ChatMessageRepository
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent, MessageType


class ChatMessageService:
    """채팅 메시지 도메인 서비스 (비동기).

    채팅 메시지 전송, 조회, 카드 공유 등의 비즈니스 로직을 담당합니다.
    Rate Limiting을 통해 메시지 전송 제한(2초에 1회)을 적용합니다.

    Attributes:
        _chat_message_repository: 채팅 메시지 저장소 (비동기)
        _rate_limiter: Rate Limiter (Redis 기반)
        _timezone: 시간대 정보
    """

    def __init__(
        self,
        chat_message_repository: ChatMessageRepository,
        rate_limiter: RateLimiter,
        timezone: ZoneInfo,
    ):
        """ChatMessageService를 초기화합니다.

        Args:
            chat_message_repository: 채팅 메시지 저장소 인터페이스
            rate_limiter: Rate Limiter 인터페이스
            timezone: 사용할 시간대 (예: ZoneInfo("Asia/Seoul"))
        """
        self._chat_message_repository = chat_message_repository
        self._rate_limiter = rate_limiter
        self._timezone = timezone

    async def send_message(
        self,
        user_id: Id,
        room_id: Id,
        content: MessageContent,
    ) -> ChatMessage:
        """일반 텍스트 메시지를 전송합니다.

        Rate Limiting을 적용하여 2초에 1회로 제한합니다.

        Args:
            user_id: 메시지 전송자 ID
            room_id: 메시지를 전송할 룸 ID
            content: 메시지 내용 (1-300자)

        Returns:
            생성된 채팅 메시지 (TEXT 타입)

        Raises:
            RateLimitExceededError: 2초 이내 중복 요청 시
        """
        # Rate Limiting 체크 (2초에 1회)
        is_allowed = await self._rate_limiter.check_rate_limit(
            user_id=user_id,
            room_id=room_id,
            window_seconds=2,
        )
        if not is_allowed:
            from bzero.domain.errors import RateLimitExceededError

            raise RateLimitExceededError

        current = datetime.now(self._timezone)
        message = ChatMessage.create(
            room_id=room_id,
            user_id=user_id,
            content=content,
            created_at=current,
            updated_at=current,
        )
        return await self._chat_message_repository.create(message)

    async def share_conversation_card(
        self,
        user_id: Id,
        room_id: Id,
        card_id: Id,
        card_question: str,
    ) -> ChatMessage:
        """대화 카드를 공유합니다.

        Rate Limiting을 적용하여 2초에 1회로 제한합니다.

        Args:
            user_id: 카드 공유자 ID
            room_id: 카드를 공유할 룸 ID
            card_id: 공유할 대화 카드 ID
            card_question: 카드의 질문 내용 (메시지 content로 사용)

        Returns:
            생성된 채팅 메시지 (CARD_SHARED 타입)

        Raises:
            RateLimitExceededError: 2초 이내 중복 요청 시
        """
        # Rate Limiting 체크 (2초에 1회)
        is_allowed = await self._rate_limiter.check_rate_limit(
            user_id=user_id,
            room_id=room_id,
            window_seconds=2,
        )
        if not is_allowed:
            from bzero.domain.errors import RateLimitExceededError

            raise RateLimitExceededError

        current = datetime.now(self._timezone)
        message = ChatMessage.create_card_shared_message(
            room_id=room_id,
            user_id=user_id,
            card_id=card_id,
            content=MessageContent(card_question),
            created_at=current,
            updated_at=current,
        )
        return await self._chat_message_repository.create(message)

    async def create_system_message(
        self,
        room_id: Id,
        content: MessageContent,
    ) -> ChatMessage:
        """시스템 메시지를 생성합니다.

        입장/퇴장/공지 등의 시스템 이벤트를 알릴 때 사용합니다.
        시스템 메시지는 Rate Limiting을 적용하지 않습니다.

        Args:
            room_id: 메시지를 전송할 룸 ID
            content: 시스템 메시지 내용

        Returns:
            생성된 시스템 메시지 (SYSTEM 타입, user_id=None)
        """
        current = datetime.now(self._timezone)
        message = ChatMessage.create_system_message(
            room_id=room_id,
            content=content,
            created_at=current,
            updated_at=current,
        )
        return await self._chat_message_repository.create(message)

    async def get_message_history(
        self,
        room_id: Id,
        cursor: Id | None = None,
        limit: int = 50,
    ) -> list[ChatMessage]:
        """룸의 메시지 히스토리를 조회합니다.

        무한 스크롤을 위한 cursor 기반 페이지네이션을 제공합니다.
        최신 메시지부터 역순으로 정렬됩니다 (created_at DESC, message_id DESC).

        Args:
            room_id: 조회할 룸 ID
            cursor: 페이지네이션 커서 (이전 응답의 마지막 message_id)
            limit: 최대 조회 개수 (기본값: 50)

        Returns:
            메시지 목록 (최신순, 최대 limit개)
        """
        return await self._chat_message_repository.find_by_room_id_paginated(
            room_id=room_id,
            cursor=cursor,
            limit=limit,
        )

    async def get_message_by_id(self, message_id: Id) -> ChatMessage:
        """메시지를 ID로 조회합니다.

        Args:
            message_id: 조회할 메시지 ID

        Returns:
            조회된 메시지

        Raises:
            NotFoundChatMessageError: 메시지를 찾을 수 없는 경우
        """
        message = await self._chat_message_repository.find_by_id(message_id)
        if message is None:
            raise NotFoundChatMessageError
        return message
