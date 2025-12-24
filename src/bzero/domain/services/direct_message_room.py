"""1:1 대화방 도메인 서비스 (비동기).

1:1 대화방의 생성, 수락, 거절, 종료 등 핵심 비즈니스 로직을 처리합니다.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from bzero.domain.entities.direct_message_room import DirectMessageRoom
from bzero.domain.errors import (
    DuplicatedDMRequestError,
    ForbiddenDMRoomAccessError,
    NotFoundDMRoomError,
    NotInSameRoomError,
)
from bzero.domain.repositories.direct_message_room import DirectMessageRoomRepository
from bzero.domain.repositories.room_stay import RoomStayRepository
from bzero.domain.value_objects import DMStatus, Id


class DirectMessageRoomService:
    """1:1 대화방 도메인 서비스 (비동기).

    1:1 대화방의 생성, 수락, 거절, 종료 등의 비즈니스 로직을 담당합니다.

    Attributes:
        _dm_room_repository: 대화방 저장소 (비동기)
        _room_stay_repository: 체류 정보 저장소 (같은 룸 검증용)
        _timezone: 시간대 정보
    """

    def __init__(
        self,
        dm_room_repository: DirectMessageRoomRepository,
        room_stay_repository: RoomStayRepository,
        timezone: ZoneInfo,
    ):
        """DirectMessageRoomService를 초기화합니다.

        Args:
            dm_room_repository: 대화방 저장소 인터페이스
            room_stay_repository: 체류 정보 저장소 인터페이스
            timezone: 사용할 시간대 (예: ZoneInfo("Asia/Seoul"))
        """
        self._dm_room_repository = dm_room_repository
        self._room_stay_repository = room_stay_repository
        self._timezone = timezone

    async def request_dm(
        self,
        requester_id: Id,
        target_id: Id,
    ) -> DirectMessageRoom:
        """1:1 대화를 신청합니다.

        같은 룸에 체류 중인 사용자에게만 대화를 신청할 수 있습니다.
        중복 신청은 불가합니다 (PENDING, ACCEPTED, ACTIVE 상태인 대화방이 이미 있는 경우).

        Args:
            requester_id: 대화 신청자 ID (user1)
            target_id: 대화 수신자 ID (user2)

        Returns:
            생성된 대화방 (status: PENDING)

        Raises:
            NotInSameRoomError: 같은 룸에 체류 중이 아닌 경우
            DuplicatedDMRequestError: 이미 활성 대화방이 존재하는 경우
        """
        # 1. 신청자의 현재 체류 정보 조회
        requester_stay = await self._room_stay_repository.find_active_by_user_id(requester_id)
        if requester_stay is None:
            raise NotInSameRoomError

        # 2. 수신자의 현재 체류 정보 조회
        target_stay = await self._room_stay_repository.find_active_by_user_id(target_id)
        if target_stay is None:
            raise NotInSameRoomError

        # 3. 같은 룸 검증
        if requester_stay.room_id.value != target_stay.room_id.value:
            raise NotInSameRoomError

        room_id = requester_stay.room_id
        guesthouse_id = requester_stay.guest_house_id

        # 4. 중복 신청 검증 (양방향)
        existing_dm_room = await self._dm_room_repository.find_by_room_and_users(
            room_id=room_id,
            user1_id=requester_id,
            user2_id=target_id,
        )
        if existing_dm_room is not None:
            raise DuplicatedDMRequestError

        # 5. 대화방 생성 (PENDING 상태)
        now = datetime.now(self._timezone)
        dm_room = DirectMessageRoom.create(
            guesthouse_id=guesthouse_id,
            room_id=room_id,
            user1_id=requester_id,
            user2_id=target_id,
            created_at=now,
            updated_at=now,
        )
        return await self._dm_room_repository.create(dm_room)

    async def accept_dm_request(
        self,
        dm_room_id: Id,
        user_id: Id,
    ) -> DirectMessageRoom:
        """1:1 대화 신청을 수락합니다.

        user2(수신자)만 수락할 수 있습니다.
        PENDING 상태인 대화방만 수락할 수 있습니다.

        Args:
            dm_room_id: 대화방 ID
            user_id: 수락하는 사용자 ID

        Returns:
            업데이트된 대화방 (status: ACCEPTED)

        Raises:
            NotFoundDMRoomError: 대화방을 찾을 수 없는 경우
            ForbiddenDMRoomAccessError: 수락 권한이 없는 경우 (user2가 아닌 경우)
            InvalidDMRoomStatusError: PENDING 상태가 아닌 경우
        """
        dm_room = await self._get_dm_room_or_raise(dm_room_id)

        # 권한 검증 (user2만 수락 가능)
        if not dm_room.can_accept_or_reject(user_id):
            raise ForbiddenDMRoomAccessError

        # 상태 전이 (엔티티 메서드)
        now = datetime.now(self._timezone)
        dm_room.accept(now)

        return await self._dm_room_repository.update(dm_room)

    async def reject_dm_request(
        self,
        dm_room_id: Id,
        user_id: Id,
    ) -> DirectMessageRoom:
        """1:1 대화 신청을 거절합니다.

        user2(수신자)만 거절할 수 있습니다.
        PENDING 상태인 대화방만 거절할 수 있습니다.

        Args:
            dm_room_id: 대화방 ID
            user_id: 거절하는 사용자 ID

        Returns:
            업데이트된 대화방 (status: REJECTED)

        Raises:
            NotFoundDMRoomError: 대화방을 찾을 수 없는 경우
            ForbiddenDMRoomAccessError: 거절 권한이 없는 경우 (user2가 아닌 경우)
            InvalidDMRoomStatusError: PENDING 상태가 아닌 경우
        """
        dm_room = await self._get_dm_room_or_raise(dm_room_id)

        # 권한 검증 (user2만 거절 가능)
        if not dm_room.can_accept_or_reject(user_id):
            raise ForbiddenDMRoomAccessError

        # 상태 전이 (엔티티 메서드)
        now = datetime.now(self._timezone)
        dm_room.reject(now)

        return await self._dm_room_repository.update(dm_room)

    async def end_dm_room(self, dm_room: DirectMessageRoom) -> DirectMessageRoom:
        """대화방을 종료합니다.

        체크아웃 시 호출됩니다.

        Args:
            dm_room: 종료할 대화방

        Returns:
            업데이트된 대화방 (status: ENDED)
        """
        now = datetime.now(self._timezone)
        dm_room.end(now)
        return await self._dm_room_repository.update(dm_room)

    async def get_dm_room_by_id(self, dm_room_id: Id) -> DirectMessageRoom:
        """ID로 대화방을 조회합니다.

        Args:
            dm_room_id: 대화방 ID

        Returns:
            조회된 대화방

        Raises:
            NotFoundDMRoomError: 대화방을 찾을 수 없는 경우
        """
        return await self._get_dm_room_or_raise(dm_room_id)

    async def get_dm_rooms_by_user(
        self,
        user_id: Id,
        statuses: list[DMStatus] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DirectMessageRoom]:
        """사용자의 대화방 목록을 조회합니다.

        Args:
            user_id: 사용자 ID
            statuses: 조회할 상태 목록 (None이면 PENDING, ACCEPTED, ACTIVE)
            limit: 최대 조회 개수 (기본 50)
            offset: 오프셋 (기본 0)

        Returns:
            대화방 목록 (최근 업데이트 순)
        """
        if statuses is None:
            statuses = [DMStatus.PENDING, DMStatus.ACCEPTED, DMStatus.ACTIVE]

        return await self._dm_room_repository.find_by_user_and_statuses(
            user_id=user_id,
            statuses=statuses,
            limit=limit,
            offset=offset,
        )

    async def count_dm_rooms_by_user(
        self,
        user_id: Id,
        statuses: list[DMStatus] | None = None,
    ) -> int:
        """사용자의 대화방 개수를 조회합니다.

        Args:
            user_id: 사용자 ID
            statuses: 조회할 상태 목록 (None이면 PENDING, ACCEPTED, ACTIVE)

        Returns:
            대화방 개수
        """
        if statuses is None:
            statuses = [DMStatus.PENDING, DMStatus.ACCEPTED, DMStatus.ACTIVE]

        return await self._dm_room_repository.count_by_user_and_statuses(
            user_id=user_id,
            statuses=statuses,
        )

    async def validate_participant(self, dm_room_id: Id, user_id: Id) -> DirectMessageRoom:
        """사용자가 대화방 참여자인지 검증합니다.

        Args:
            dm_room_id: 대화방 ID
            user_id: 사용자 ID

        Returns:
            검증된 대화방

        Raises:
            NotFoundDMRoomError: 대화방을 찾을 수 없는 경우
            ForbiddenDMRoomAccessError: 참여자가 아닌 경우
        """
        dm_room = await self._get_dm_room_or_raise(dm_room_id)
        if not dm_room.is_participant(user_id):
            raise ForbiddenDMRoomAccessError
        return dm_room

    async def _get_dm_room_or_raise(self, dm_room_id: Id) -> DirectMessageRoom:
        """대화방을 조회하거나 예외를 발생시킵니다."""
        dm_room = await self._dm_room_repository.find_by_id(dm_room_id)
        if dm_room is None:
            raise NotFoundDMRoomError
        return dm_room
