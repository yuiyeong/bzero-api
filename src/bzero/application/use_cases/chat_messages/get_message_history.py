"""메시지 히스토리 조회 유스케이스.

룸의 메시지 히스토리를 cursor 기반 페이지네이션으로 조회하는 비즈니스 로직을 담당합니다.
"""

from bzero.application.results import ChatMessageResult
from bzero.domain.services import ChatMessageService, RoomStayService, UserService
from bzero.domain.value_objects import AuthProvider, Id


class GetMessageHistoryUseCase:
    """메시지 히스토리 조회 유스케이스.

    무한 스크롤을 위한 cursor 기반 페이지네이션을 제공합니다.
    사용자가 해당 룸에 체류 중인지 검증합니다.
    """

    def __init__(
        self,
        user_service: UserService,
        chat_message_service: ChatMessageService,
        room_stay_service: RoomStayService,
    ):
        """GetMessageHistoryUseCase를 초기화합니다.

        Args:
            user_service: 사용자 도메인 서비스
            chat_message_service: 채팅 메시지 도메인 서비스
            room_stay_service: 룸 스테이 도메인 서비스
        """
        self._user_service = user_service
        self._chat_message_service = chat_message_service
        self._room_stay_service = room_stay_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
        room_id: str,
        cursor: str | None = None,
        limit: int = 50,
    ) -> list[ChatMessageResult]:
        """메시지 히스토리 조회를 실행합니다.

        Args:
            provider_user_id:
            provider:
            room_id: 조회할 룸 ID (hex 문자열)
            cursor: 페이지네이션 커서 (이전 응답의 마지막 message_id)
            limit: 최대 조회 개수 (기본값: 50)

        Returns:
            메시지 목록 (최신순, 최대 limit개)

        Raises:
            ForbiddenRoomForUserError: 사용자가 해당 룸에 체류 중이지 않은 경우

        """
        # 0. 사용자 ID 검증
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        # 1. 사용자가 해당 룸에 체류 중인지 검증
        await self._room_stay_service.get_stays_by_user_id_and_room_id(
            user_id=user.user_id,
            room_id=Id.from_hex(room_id),
        )

        # 2. 메시지 히스토리 조회 (cursor 기반 페이지네이션)
        messages = await self._chat_message_service.get_message_history(
            room_id=Id.from_hex(room_id),
            cursor=Id.from_hex(cursor) if cursor else None,
            limit=limit,
        )

        return [ChatMessageResult.create_from(msg) for msg in messages]
