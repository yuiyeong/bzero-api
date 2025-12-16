from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bzero.domain.entities import Room, RoomStay, Ticket
from bzero.domain.errors import ForbiddenRoomForUserError, InvalidTicketStatusError
from bzero.domain.repositories.room_stay import RoomStayRepository, RoomStaySyncRepository
from bzero.domain.value_objects import Id


class RoomStayService:
    """체류 도메인 서비스 (비동기).

    체류 관련 비즈니스 로직을 처리합니다.
    """

    def __init__(self, room_stay_repository: RoomStayRepository):
        """RoomStayService를 초기화합니다.

        Args:
            room_stay_repository: 체류 비동기 리포지토리
        """
        self._room_stay_repository = room_stay_repository

    async def get_checked_in_by_user_id(self, user_id: Id) -> RoomStay | None:
        """사용자의 현재 활성 체류를 조회합니다.

        Args:
            user_id: 사용자 ID

        Returns:
            활성(CHECKED_IN) 체류 엔티티 또는 None
        """
        return await self._room_stay_repository.find_checked_in_by_user_id(user_id)

    async def get_stays_by_user_id_and_room_id(self, user_id: Id, room_id: Id) -> list[RoomStay]:
        stays = await self._room_stay_repository.find_all_checked_in_by_room_id(room_id)
        if all(user_id != stay.user_id for stay in stays):
            # 사용자에 해당하는 체류 정보가 없다면,
            raise ForbiddenRoomForUserError
        return stays


class RoomStaySyncService:
    """체류 도메인 서비스 (동기).

    Celery 백그라운드 태스크에서 체류 관련 비즈니스 로직을 처리합니다.
    체크인 및 방 배정 기능을 제공합니다.
    """

    ROOM_STAY_DURATION_IN_HOUR = 24
    """기본 체류 시간 (시간 단위)"""

    def __init__(
        self,
        room_stay_sync_repository: RoomStaySyncRepository,
        timezone: ZoneInfo,
    ) -> None:
        """RoomStaySyncService를 초기화합니다.

        Args:
            room_stay_sync_repository: 체류 동기 리포지토리
            timezone: 시간대 정보
        """
        self._room_stay_repository = room_stay_sync_repository
        self._timezone = timezone

    def assign_room(self, ticket: Ticket, room: Room) -> RoomStay:
        """티켓으로 방에 체크인합니다.

        COMPLETED 상태의 티켓을 사용하여 방에 체류 기록을 생성합니다.
        체크아웃 예정 시간은 체크인 시간 + 24시간으로 설정됩니다.

        Args:
            ticket: 체크인에 사용할 티켓 (COMPLETED 상태여야 함)
            room: 배정할 방 엔티티

        Returns:
            생성된 체류 엔티티 (CHECKED_IN 상태)

        Raises:
            InvalidTicketStatusError: 티켓이 COMPLETED 상태가 아닌 경우
        """
        if not ticket.is_completed:
            raise InvalidTicketStatusError

        check_in_at = datetime.now(self._timezone)
        scheduled_check_out_at = check_in_at + timedelta(hours=self.ROOM_STAY_DURATION_IN_HOUR)
        room_stay = RoomStay.create(
            user_id=ticket.user_id,
            city_id=ticket.city_snapshot.city_id,
            guest_house_id=room.guest_house_id,
            room_id=room.room_id,
            ticket_id=ticket.ticket_id,
            check_in_at=check_in_at,
            scheduled_check_out_at=scheduled_check_out_at,
            created_at=check_in_at,
            updated_at=check_in_at,
        )
        return self._room_stay_repository.create(room_stay)
