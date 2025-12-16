"""RoomStaySyncService 단위 테스트"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.entities import Airship, City, Room, Ticket
from bzero.domain.errors import InvalidTicketStatusError
from bzero.domain.repositories.room_stay import RoomStaySyncRepository
from bzero.domain.services.room_stay import RoomStaySyncService
from bzero.domain.value_objects import Id, TicketStatus
from bzero.domain.value_objects.room_stay import RoomStayStatus


@pytest.fixture
def mock_room_stay_repository() -> MagicMock:
    """Mock RoomStaySyncRepository"""
    return MagicMock(spec=RoomStaySyncRepository)


@pytest.fixture
def room_stay_service(
    mock_room_stay_repository: MagicMock,
) -> RoomStaySyncService:
    """RoomStaySyncService with mocked repositories"""
    timezone = get_settings().timezone
    return RoomStaySyncService(mock_room_stay_repository, timezone)


@pytest.fixture
def sample_user_id() -> Id:
    """샘플 유저 ID"""
    return Id(uuid7())


@pytest.fixture
def sample_city() -> City:
    """샘플 도시"""
    now = datetime.now(get_settings().timezone)
    return City(
        city_id=Id(uuid7()),
        name="세렌시아",
        theme="관계",
        image_url="https://example.com/serencia.jpg",
        description="노을빛 항구 마을",
        base_cost_points=300,
        base_duration_hours=24,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_airship() -> Airship:
    """샘플 비행선"""
    now = datetime.now(get_settings().timezone)
    return Airship(
        airship_id=Id(uuid7()),
        name="일반 비행선",
        description="편안하고 여유로운 여행",
        image_url="https://example.com/normal.jpg",
        cost_factor=1,
        duration_factor=1,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_completed_ticket(sample_user_id: Id, sample_city: City, sample_airship: Airship) -> Ticket:
    """완료된 티켓"""
    now = datetime.now(get_settings().timezone)
    ticket = Ticket.create(
        user_id=sample_user_id,
        city_snapshot=sample_city.snapshot(),
        airship_snapshot=sample_airship.snapshot(),
        cost_points=300,
        departure_datetime=now,
        arrival_datetime=now + timedelta(hours=24),
        created_at=now,
        updated_at=now,
    )
    # PURCHASED -> BOARDING -> COMPLETED
    ticket.consume()
    ticket.complete()
    return ticket


@pytest.fixture
def sample_boarding_ticket(sample_user_id: Id, sample_city: City, sample_airship: Airship) -> Ticket:
    """탑승 중인 티켓 (미완료)"""
    now = datetime.now(get_settings().timezone)
    ticket = Ticket.create(
        user_id=sample_user_id,
        city_snapshot=sample_city.snapshot(),
        airship_snapshot=sample_airship.snapshot(),
        cost_points=300,
        departure_datetime=now,
        arrival_datetime=now + timedelta(hours=24),
        created_at=now,
        updated_at=now,
    )
    # PURCHASED -> BOARDING
    ticket.consume()
    return ticket


@pytest.fixture
def sample_room() -> Room:
    """샘플 방 (정원 여유 있음)"""
    now = datetime.now(get_settings().timezone)
    room = Room.create(
        guest_house_id=Id(uuid7()),
        max_capacity=6,
        created_at=now,
        updated_at=now,
    )
    room.current_capacity = 3  # 3명 체류 중
    return room


class TestRoomStaySyncServiceAssignRoom:
    """assign_room 메서드 테스트"""

    def test_assign_room_success(
        self,
        room_stay_service: RoomStaySyncService,
        mock_room_stay_repository: MagicMock,
        sample_completed_ticket: Ticket,
        sample_room: Room,
    ):
        """완료된 티켓으로 방 배정에 성공한다"""
        # Given
        assert sample_completed_ticket.is_completed

        def create_room_stay(room_stay):
            return room_stay

        mock_room_stay_repository.create = MagicMock(side_effect=create_room_stay)

        # When
        room_stay = room_stay_service.assign_room(sample_completed_ticket, sample_room)

        # Then
        assert room_stay.user_id == sample_completed_ticket.user_id
        assert room_stay.city_id == sample_completed_ticket.city_snapshot.city_id
        assert room_stay.guest_house_id == sample_room.guest_house_id
        assert room_stay.room_id == sample_room.room_id
        assert room_stay.ticket_id == sample_completed_ticket.ticket_id
        assert room_stay.status == RoomStayStatus.CHECKED_IN
        mock_room_stay_repository.create.assert_called_once()

    def test_assign_room_raises_invalid_ticket_status_error(
        self,
        room_stay_service: RoomStaySyncService,
        sample_boarding_ticket: Ticket,
        sample_room: Room,
    ):
        """완료되지 않은 티켓이면 InvalidTicketStatusError를 발생시킨다"""
        # Given
        assert not sample_boarding_ticket.is_completed
        assert sample_boarding_ticket.status == TicketStatus.BOARDING

        # When/Then
        with pytest.raises(InvalidTicketStatusError):
            room_stay_service.assign_room(sample_boarding_ticket, sample_room)

    def test_assign_room_creates_room_stay_with_correct_check_out_time(
        self,
        room_stay_service: RoomStaySyncService,
        mock_room_stay_repository: MagicMock,
        sample_completed_ticket: Ticket,
        sample_room: Room,
    ):
        """체크아웃 시간이 24시간 후로 설정된다"""
        # Given
        captured_room_stay = None

        def create_room_stay(room_stay):
            nonlocal captured_room_stay
            captured_room_stay = room_stay
            return room_stay

        mock_room_stay_repository.create = MagicMock(side_effect=create_room_stay)

        # When
        room_stay_service.assign_room(sample_completed_ticket, sample_room)

        # Then
        assert captured_room_stay is not None
        duration = captured_room_stay.scheduled_check_out_at - captured_room_stay.check_in_at
        expected_duration = timedelta(hours=RoomStaySyncService.ROOM_STAY_DURATION_IN_HOUR)
        assert duration == expected_duration
        assert duration.total_seconds() / 3600 == 24

    def test_assign_room_raises_error_when_ticket_is_purchased(
        self,
        room_stay_service: RoomStaySyncService,
        sample_user_id: Id,
        sample_city: City,
        sample_airship: Airship,
        sample_room: Room,
    ):
        """PURCHASED 상태 티켓으로 방 배정 시 InvalidTicketStatusError를 발생시킨다"""
        # Given: PURCHASED 상태의 티켓
        now = datetime.now(get_settings().timezone)
        purchased_ticket = Ticket.create(
            user_id=sample_user_id,
            city_snapshot=sample_city.snapshot(),
            airship_snapshot=sample_airship.snapshot(),
            cost_points=300,
            departure_datetime=now,
            arrival_datetime=now + timedelta(hours=24),
            created_at=now,
            updated_at=now,
        )
        assert purchased_ticket.status == TicketStatus.PURCHASED
        assert not purchased_ticket.is_completed

        # When/Then
        with pytest.raises(InvalidTicketStatusError):
            room_stay_service.assign_room(purchased_ticket, sample_room)

    def test_assign_room_raises_error_when_ticket_is_cancelled(
        self,
        room_stay_service: RoomStaySyncService,
        sample_user_id: Id,
        sample_city: City,
        sample_airship: Airship,
        sample_room: Room,
    ):
        """CANCELLED 상태 티켓으로 방 배정 시 InvalidTicketStatusError를 발생시킨다"""
        # Given: CANCELLED 상태의 티켓
        now = datetime.now(get_settings().timezone)
        cancelled_ticket = Ticket.create(
            user_id=sample_user_id,
            city_snapshot=sample_city.snapshot(),
            airship_snapshot=sample_airship.snapshot(),
            cost_points=300,
            departure_datetime=now,
            arrival_datetime=now + timedelta(hours=24),
            created_at=now,
            updated_at=now,
        )
        cancelled_ticket.cancel()
        assert cancelled_ticket.status == TicketStatus.CANCELLED
        assert not cancelled_ticket.is_completed

        # When/Then
        with pytest.raises(InvalidTicketStatusError):
            room_stay_service.assign_room(cancelled_ticket, sample_room)
