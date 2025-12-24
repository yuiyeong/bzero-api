"""1:1 메시지 도메인 서비스 (비동기).

1:1 대화 메시지의 전송, 조회, 읽음 처리 등 핵심 비즈니스 로직을 처리합니다.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from bzero.domain.entities.direct_message import DirectMessage
from bzero.domain.entities.direct_message_room import DirectMessageRoom
from bzero.domain.errors import (
    ForbiddenDMRoomAccessError,
    InvalidDMRoomStatusError,
    NotFoundDMMessageError,
    RateLimitExceededError,
)
from bzero.domain.ports.rate_limiter import RateLimiter
from bzero.domain.repositories.direct_message import DirectMessageRepository
from bzero.domain.repositories.direct_message_room import DirectMessageRoomRepository
from bzero.domain.value_objects import DMStatus, Id
from bzero.domain.value_objects.chat_message import MessageContent


class DirectMessageService:
    """1:1 메시지 도메인 서비스 (비동기).

    1:1 메시지 전송, 조회, 읽음 처리 등의 비즈니스 로직을 담당합니다.
    Rate Limiting을 통해 메시지 전송 제한(2초에 1회)을 적용합니다.

    Attributes:
        _dm_repository: 메시지 저장소 (비동기)
        _dm_room_repository: 대화방 저장소 (상태 업데이트용)
        _rate_limiter: Rate Limiter (Redis 기반)
        _timezone: 시간대 정보
    """

    def __init__(
        self,
        dm_repository: DirectMessageRepository,
        dm_room_repository: DirectMessageRoomRepository,
        rate_limiter: RateLimiter,
        timezone: ZoneInfo,
    ):
        """DirectMessageService를 초기화합니다.

        Args:
            dm_repository: 메시지 저장소 인터페이스
            dm_room_repository: 대화방 저장소 인터페이스
            rate_limiter: Rate Limiter 인터페이스
            timezone: 사용할 시간대 (예: ZoneInfo("Asia/Seoul"))
        """
        self._dm_repository = dm_repository
        self._dm_room_repository = dm_room_repository
        self._rate_limiter = rate_limiter
        self._timezone = timezone

    async def send_message(
        self,
        dm_room: DirectMessageRoom,
        from_user_id: Id,
        content: MessageContent,
    ) -> tuple[DirectMessage, DirectMessageRoom]:
        """메시지를 전송합니다.

        Rate Limiting을 적용하여 2초에 1회로 제한합니다.
        첫 메시지 전송 시 대화방 상태를 ACCEPTED → ACTIVE로 전환합니다.

        Args:
            dm_room: 대화방 엔티티
            from_user_id: 발신자 ID
            content: 메시지 내용 (1-300자)

        Returns:
            (생성된 메시지, 업데이트된 대화방) 튜플

        Raises:
            ForbiddenDMRoomAccessError: 참여자가 아닌 경우
            InvalidDMRoomStatusError: 메시지 전송 불가 상태인 경우
            RateLimitExceededError: 2초 이내 중복 요청 시
        """
        # 1. 참여자 검증
        if not dm_room.is_participant(from_user_id):
            raise ForbiddenDMRoomAccessError

        # 2. 상태 검증 (ACCEPTED 또는 ACTIVE만 전송 가능)
        if not dm_room.can_send_message():
            raise InvalidDMRoomStatusError

        # 3. Rate Limiting 체크 (2초에 1회)
        is_allowed = await self._rate_limiter.check_rate_limit(
            user_id=from_user_id,
            room_id=dm_room.dm_room_id,  # DM용 rate limit key
            window_seconds=2,
        )
        if not is_allowed:
            raise RateLimitExceededError

        now = datetime.now(self._timezone)

        # 4. 첫 메시지인 경우 상태 전환 (ACCEPTED → ACTIVE)
        if dm_room.status == DMStatus.ACCEPTED:
            dm_room.activate(now)
            dm_room = await self._dm_room_repository.update(dm_room)

        # 5. 메시지 생성
        to_user_id = dm_room.get_other_user_id(from_user_id)
        message = DirectMessage.create(
            dm_room_id=dm_room.dm_room_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            content=content,
            created_at=now,
            updated_at=now,
        )
        created_message = await self._dm_repository.create(message)

        return created_message, dm_room

    async def get_message_history(
        self,
        dm_room_id: Id,
        cursor: Id | None = None,
        limit: int = 50,
    ) -> list[DirectMessage]:
        """대화방의 메시지 히스토리를 조회합니다.

        무한 스크롤을 위한 cursor 기반 페이지네이션을 제공합니다.
        오래된 메시지부터 순서대로 정렬됩니다 (created_at ASC, dm_id ASC).

        Args:
            dm_room_id: 대화방 ID
            cursor: 페이지네이션 커서 (이전 응답의 마지막 dm_id)
            limit: 최대 조회 개수 (기본값: 50)

        Returns:
            메시지 목록 (오래된 순, 최대 limit개)
        """
        return await self._dm_repository.find_by_dm_room_paginated(
            dm_room_id=dm_room_id,
            cursor=cursor,
            limit=limit,
        )

    async def mark_as_read(
        self,
        dm_room_id: Id,
        user_id: Id,
    ) -> int:
        """대화방의 메시지를 읽음 처리합니다.

        자신이 수신한 메시지(to_user_id == user_id)를 모두 읽음 처리합니다.

        Args:
            dm_room_id: 대화방 ID
            user_id: 읽음 처리할 사용자 ID

        Returns:
            읽음 처리된 메시지 개수
        """
        return await self._dm_repository.mark_as_read_by_dm_room_and_user(
            dm_room_id=dm_room_id,
            user_id=user_id,
        )

    async def count_unread(
        self,
        dm_room_id: Id,
        user_id: Id,
    ) -> int:
        """읽지 않은 메시지 개수를 조회합니다.

        Args:
            dm_room_id: 대화방 ID
            user_id: 수신자 ID

        Returns:
            읽지 않은 메시지 개수
        """
        return await self._dm_repository.count_unread_by_dm_room_and_user(
            dm_room_id=dm_room_id,
            user_id=user_id,
        )

    async def get_latest_message(self, dm_room_id: Id) -> DirectMessage | None:
        """대화방의 가장 최근 메시지를 조회합니다.

        대화방 목록에서 마지막 메시지를 표시할 때 사용합니다.

        Args:
            dm_room_id: 대화방 ID

        Returns:
            최근 메시지 또는 None
        """
        return await self._dm_repository.find_latest_by_dm_room(dm_room_id)

    async def get_message_by_id(self, dm_id: Id) -> DirectMessage:
        """ID로 메시지를 조회합니다.

        Args:
            dm_id: 메시지 ID

        Returns:
            조회된 메시지

        Raises:
            NotFoundDMMessageError: 메시지를 찾을 수 없는 경우
        """
        message = await self._dm_repository.find_by_id(dm_id)
        if message is None:
            raise NotFoundDMMessageError
        return message
