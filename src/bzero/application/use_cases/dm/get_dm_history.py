"""메시지 히스토리 조회 유스케이스.

사용자가 1:1 대화방의 메시지 히스토리를 조회합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.dm import DirectMessageResult
from bzero.domain.errors import UnauthorizedError
from bzero.domain.services.direct_message import DirectMessageService
from bzero.domain.services.direct_message_room import DirectMessageRoomService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import AuthProvider, Id


class GetDMHistoryUseCase:
    """메시지 히스토리 조회 유스케이스.

    사용자가 1:1 대화방의 메시지 히스토리를 조회합니다.
    cursor 기반 페이지네이션을 제공합니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        dm_room_service: DirectMessageRoomService,
        dm_service: DirectMessageService,
        user_service: UserService,
    ):
        """GetDMHistoryUseCase를 초기화합니다.

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
        user_id: str | None = None,
        provider: str | None = None,
        provider_user_id: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
        mark_as_read: bool = False,
    ) -> list[DirectMessageResult]:
        """대화 히스토리를 조회합니다.

        Args:
            dm_room_id: 대화방 ID
            user_id: 사용자 ID (Internal). provider 정보가 없을 경우 필수.
            provider: 인증 제공자. user_id가 없을 경우 필수.
            provider_user_id: 인증 제공자의 사용자 ID. user_id가 없을 경우 필수.
            cursor: 페이지네이션 커서
            limit: 조회 개수
            mark_as_read: 읽음 처리 여부

        Returns:
            메시지 목록

        Raises:
            UnauthorizedError: 사용자 식별 정보가 부족하거나 잘못된 경우
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

        dm_room_id_vo = Id.from_hex(dm_room_id)
        user_id_vo = Id.from_hex(user_id)

        # 1. 대화방 접근 권한 검증
        await self._dm_room_service.validate_participant(dm_room_id_vo, user_id_vo)

        # 2. 메시지 히스토리 조회
        cursor_id = Id.from_hex(cursor) if cursor else None
        messages = await self._dm_service.get_message_history(
            dm_room_id=dm_room_id_vo,
            cursor=cursor_id,
            limit=limit,
        )

        # 3. 읽음 처리 (선택적)
        if mark_as_read:
            await self._dm_service.mark_as_read(
                dm_room_id=dm_room_id_vo,
                user_id=user_id_vo,
            )

        # 4. 트랜잭션 커밋 (읽음 처리한 경우에만 필요)
        if mark_as_read:
            await self._session.commit()

        return [DirectMessageResult.create_from(msg) for msg in messages]
