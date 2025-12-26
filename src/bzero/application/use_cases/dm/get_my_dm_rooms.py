"""내 대화방 목록 조회 유스케이스.

사용자의 1:1 대화방 목록을 조회합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.dm import DirectMessageRoomResult
from bzero.domain.errors import UnauthorizedError
from bzero.domain.services.direct_message import DirectMessageService
from bzero.domain.services.direct_message_room import DirectMessageRoomService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import AuthProvider, DMStatus


class GetMyDMRoomsUseCase:
    """내 대화방 목록 조회 유스케이스.

    사용자가 참여 중인 1:1 대화방 목록을 조회합니다.
    각 대화방의 마지막 메시지와 읽지 않은 메시지 개수를 함께 반환합니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        dm_room_service: DirectMessageRoomService,
        dm_service: DirectMessageService,
        user_service: UserService,
    ):
        """GetMyDMRoomsUseCase를 초기화합니다.

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
        provider: str,
        provider_user_id: str,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[DirectMessageRoomResult]:
        """나의 대화방 목록 조회를 실행합니다.

        Args:
            provider: 인증 제공자
            provider_user_id: 인증 제공자의 사용자 ID
            status: 대화방 상태 필터 (pending, accepted, active, ended, None=all active)
            limit: 최대 조회 개수 (기본값: 20)
            offset: 오프셋 (기본값: 0)

        Returns:
            대화방 목록 (최근 업데이트 순)

        Raises:
            UnauthorizedError: 사용자를 찾을 수 없는 경우
        """
        # 1. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )
        if not user:
            raise UnauthorizedError("User not found.")

        user_id_vo = user.user_id

        # 상태 필터 처리
        statuses: list[DMStatus] | None = None
        if status:
            statuses = [DMStatus(status)]

        # 1. 대화방 목록 조회
        dm_rooms = await self._dm_room_service.get_dm_rooms_by_user(
            user_id=user_id_vo,
            statuses=statuses,
            limit=limit,
            offset=offset,
        )

        # 2. 각 대화방의 마지막 메시지와 읽지 않은 메시지 개수 조회
        results = []
        for dm_room in dm_rooms:
            # 마지막 메시지 조회
            last_message = await self._dm_service.get_latest_message(dm_room.dm_room_id)

            # 읽지 않은 메시지 개수 조회
            unread_count = await self._dm_service.count_unread(
                dm_room_id=dm_room.dm_room_id,
                user_id=user_id_vo,
            )

            results.append(
                DirectMessageRoomResult.create_from(
                    dm_room,
                    last_message=last_message,
                    unread_count=unread_count,
                )
            )

        return results
