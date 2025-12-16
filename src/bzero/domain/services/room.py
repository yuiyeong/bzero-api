from datetime import datetime
from zoneinfo import ZoneInfo

from bzero.domain.entities import Room
from bzero.domain.repositories.room import RoomSyncRepository
from bzero.domain.value_objects import Id


class RoomSyncService:
    """방 도메인 서비스 (동기).

    Celery 백그라운드 태스크에서 방 관련 비즈니스 로직을 처리합니다.
    방 배정 및 인원 관리 기능을 제공합니다.
    """

    MAX_CAPACITY = 6
    """방 최대 수용 인원"""

    def __init__(self, room_sync_repository: RoomSyncRepository, timezone: ZoneInfo):
        """RoomSyncService를 초기화합니다.

        Args:
            room_sync_repository: 방 동기 리포지토리
            timezone: 시간대 정보
        """
        self._room_repository = room_sync_repository
        self._timezone = timezone

    def get_or_create_room_for_update(self, guesthouse_id: Id) -> Room:
        """게스트하우스에서 배정 가능한 방을 조회하거나 새로 생성합니다.

        배정 가능한 방(만원이 아닌 방)이 있으면 반환하고,
        없으면 새 방을 생성하여 반환합니다.
        동시성 제어를 위해 FOR UPDATE 락을 사용합니다.

        Args:
            guesthouse_id: 게스트하우스 ID

        Returns:
            배정 가능한 방 또는 새로 생성된 방 엔티티
        """
        available_rooms = self._room_repository.find_available_by_guest_house_id_for_update(guesthouse_id)
        if available_rooms:
            return available_rooms[0]

        now = datetime.now(self._timezone)
        room = Room.create(guest_house_id=guesthouse_id, max_capacity=self.MAX_CAPACITY, created_at=now, updated_at=now)
        return self._room_repository.create(room)

    def occupy_room(self, room: Room) -> Room:
        """방에 여행자를 배정합니다.

        방의 현재 인원을 1 증가시킵니다.

        Args:
            room: 배정할 방 엔티티

        Returns:
            업데이트된 방 엔티티

        Raises:
            InvalidRoomStatusError: 방이 이미 만원인 경우
        """
        room.increase_capacity()
        return self._room_repository.update(room)
