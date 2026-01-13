from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.orm import Session
from uuid_utils import uuid7

from bzero.domain.entities import Airship, City, Ticket
from bzero.domain.entities.room import Room
from bzero.domain.errors import InvalidTicketStatusError
from bzero.domain.services.room_stay import RoomStaySyncService
from bzero.domain.value_objects import GuestHouseType, Id, RoomStayStatus, TicketStatus
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.room_model import RoomModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.room import SqlAlchemyRoomSyncRepository
from bzero.infrastructure.repositories.room_stay import SqlAlchemyRoomStaySyncRepository


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone"""
    return ZoneInfo("Asia/Seoul")


@pytest.fixture
def room_stay_sync_service(test_sync_session: Session, timezone: ZoneInfo) -> RoomStaySyncService:
    """RoomStaySyncService fixture를 생성합니다."""
    room_stay_repository = SqlAlchemyRoomStaySyncRepository(test_sync_session)
    room_repository = SqlAlchemyRoomSyncRepository(test_sync_session)
    return RoomStaySyncService(room_stay_repository, room_repository, timezone)


@pytest.fixture
def sync_sample_user(test_sync_session: Session) -> UserModel:
    """테스트용 샘플 유저 데이터를 생성합니다."""
    now = datetime.now()
    user_model = UserModel(
        user_id=uuid7(),
        email="test@example.com",
        nickname="테스트유저",
        profile_emoji="🌟",
        current_points=1000,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(user_model)
    test_sync_session.flush()
    return user_model


@pytest.fixture
def sync_sample_city(test_sync_session: Session) -> CityModel:
    """테스트용 샘플 도시 데이터를 생성합니다."""
    now = datetime.now()
    city_model = CityModel(
        city_id=uuid7(),
        name="세렌시아",
        theme="관계",
        image_url="https://example.com/serencia.jpg",
        description="노을빛 항구 마을",
        base_cost_points=300,
        base_duration_minutes=24,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(city_model)
    test_sync_session.flush()
    return city_model


@pytest.fixture
def sync_sample_airship(test_sync_session: Session) -> AirshipModel:
    """테스트용 샘플 비행선 데이터를 생성합니다."""
    now = datetime.now()
    airship_model = AirshipModel(
        airship_id=uuid7(),
        name="일반 비행선",
        description="편안하고 여유로운 여행을 원하는 여행자를 위한 비행선",
        image_url="https://example.com/normal.jpg",
        cost_factor=1,
        duration_factor=1,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(airship_model)
    test_sync_session.flush()
    return airship_model


@pytest.fixture
def sync_sample_guest_house(test_sync_session: Session, sync_sample_city: CityModel) -> GuestHouseModel:
    """테스트용 샘플 게스트하우스 데이터를 생성합니다."""
    now = datetime.now()
    guest_house_model = GuestHouseModel(
        guest_house_id=uuid7(),
        city_id=sync_sample_city.city_id,
        guest_house_type=GuestHouseType.MIXED.value,
        name="편안한 게스트하우스",
        description="조용하고 편안한 공간",
        image_url="https://example.com/guesthouse1.jpg",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(guest_house_model)
    test_sync_session.flush()
    return guest_house_model


@pytest.fixture
def sync_sample_room(test_sync_session: Session, sync_sample_guest_house: GuestHouseModel) -> RoomModel:
    """테스트용 샘플 방 데이터를 생성합니다."""
    now = datetime.now()
    room_model = RoomModel(
        room_id=uuid7(),
        guest_house_id=sync_sample_guest_house.guest_house_id,
        max_capacity=6,
        current_capacity=1,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(room_model)
    test_sync_session.flush()
    return room_model


def _create_city_entity(city_model: CityModel) -> City:
    """CityModel을 City 엔티티로 변환합니다."""
    return City(
        city_id=Id(city_model.city_id),
        name=city_model.name,
        theme=city_model.theme,
        image_url=city_model.image_url,
        description=city_model.description,
        base_cost_points=city_model.base_cost_points,
        base_duration_minutes=city_model.base_duration_minutes,
        display_order=city_model.display_order,
        is_active=city_model.is_active,
        created_at=city_model.created_at,
        updated_at=city_model.updated_at,
    )


def _create_airship_entity(airship_model: AirshipModel) -> Airship:
    """AirshipModel을 Airship 엔티티로 변환합니다."""
    return Airship(
        airship_id=Id(airship_model.airship_id),
        name=airship_model.name,
        description=airship_model.description,
        image_url=airship_model.image_url,
        cost_factor=airship_model.cost_factor,
        duration_factor=airship_model.duration_factor,
        display_order=airship_model.display_order,
        is_active=airship_model.is_active,
        created_at=airship_model.created_at,
        updated_at=airship_model.updated_at,
    )


def _create_room_entity(room_model: RoomModel) -> Room:
    """RoomModel을 Room 엔티티로 변환합니다."""
    return Room(
        room_id=Id(room_model.room_id),
        guest_house_id=Id(room_model.guest_house_id),
        max_capacity=room_model.max_capacity,
        current_capacity=room_model.current_capacity,
        created_at=room_model.created_at,
        updated_at=room_model.updated_at,
    )


@pytest.fixture
def sync_sample_completed_ticket(
    test_sync_session: Session,
    sync_sample_user: UserModel,
    sync_sample_city: CityModel,
    sync_sample_airship: AirshipModel,
    timezone: ZoneInfo,
) -> Ticket:
    """테스트용 COMPLETED 상태 티켓 데이터를 생성합니다."""
    now = datetime.now(timezone)
    city = _create_city_entity(sync_sample_city)
    airship = _create_airship_entity(sync_sample_airship)

    ticket = Ticket.create(
        user_id=Id(sync_sample_user.user_id),
        city_snapshot=city.snapshot(),
        airship_snapshot=airship.snapshot(),
        cost_points=300,
        departure_datetime=now - timedelta(hours=24),
        arrival_datetime=now,
        created_at=now - timedelta(hours=24),
        updated_at=now,
    )
    # PURCHASED -> BOARDING -> COMPLETED
    ticket.consume()
    ticket.complete()

    ticket_model = TicketModel(
        ticket_id=ticket.ticket_id.value,
        user_id=ticket.user_id.value,
        ticket_number=ticket.ticket_number,
        cost_points=ticket.cost_points,
        status=ticket.status.value,
        departure_datetime=ticket.departure_datetime,
        arrival_datetime=ticket.arrival_datetime,
        city_id=ticket.city_snapshot.city_id.value,
        city_name=ticket.city_snapshot.name,
        city_theme=ticket.city_snapshot.theme,
        city_image_url=ticket.city_snapshot.image_url,
        city_description=ticket.city_snapshot.description,
        city_base_cost_points=ticket.city_snapshot.base_cost_points,
        city_base_duration_minutes=ticket.city_snapshot.base_duration_minutes,
        airship_id=ticket.airship_snapshot.airship_id.value,
        airship_name=ticket.airship_snapshot.name,
        airship_image_url=ticket.airship_snapshot.image_url,
        airship_description=ticket.airship_snapshot.description,
        airship_cost_factor=ticket.airship_snapshot.cost_factor,
        airship_duration_factor=ticket.airship_snapshot.duration_factor,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )
    test_sync_session.add(ticket_model)
    test_sync_session.flush()

    return ticket


@pytest.fixture
def sync_sample_boarding_ticket(
    test_sync_session: Session,
    sync_sample_user: UserModel,
    sync_sample_city: CityModel,
    sync_sample_airship: AirshipModel,
    timezone: ZoneInfo,
) -> Ticket:
    """테스트용 BOARDING 상태 티켓 데이터를 생성합니다."""
    now = datetime.now(timezone)
    city = _create_city_entity(sync_sample_city)
    airship = _create_airship_entity(sync_sample_airship)

    ticket = Ticket.create(
        user_id=Id(sync_sample_user.user_id),
        city_snapshot=city.snapshot(),
        airship_snapshot=airship.snapshot(),
        cost_points=300,
        departure_datetime=now,
        arrival_datetime=now + timedelta(hours=24),
        created_at=now,
        updated_at=now,
    )
    # PURCHASED -> BOARDING
    ticket.consume()

    ticket_model = TicketModel(
        ticket_id=ticket.ticket_id.value,
        user_id=ticket.user_id.value,
        ticket_number=ticket.ticket_number,
        cost_points=ticket.cost_points,
        status=ticket.status.value,
        departure_datetime=ticket.departure_datetime,
        arrival_datetime=ticket.arrival_datetime,
        city_id=ticket.city_snapshot.city_id.value,
        city_name=ticket.city_snapshot.name,
        city_theme=ticket.city_snapshot.theme,
        city_image_url=ticket.city_snapshot.image_url,
        city_description=ticket.city_snapshot.description,
        city_base_cost_points=ticket.city_snapshot.base_cost_points,
        city_base_duration_minutes=ticket.city_snapshot.base_duration_minutes,
        airship_id=ticket.airship_snapshot.airship_id.value,
        airship_name=ticket.airship_snapshot.name,
        airship_image_url=ticket.airship_snapshot.image_url,
        airship_description=ticket.airship_snapshot.description,
        airship_cost_factor=ticket.airship_snapshot.cost_factor,
        airship_duration_factor=ticket.airship_snapshot.duration_factor,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )
    test_sync_session.add(ticket_model)
    test_sync_session.flush()

    return ticket


class TestRoomStaySyncServiceAssignRoom:
    """assign_room 메서드 통합 테스트"""

    def test_assign_room_success(
        self,
        room_stay_sync_service: RoomStaySyncService,
        sync_sample_completed_ticket: Ticket,
        sync_sample_room: RoomModel,
    ):
        """COMPLETED 상태 티켓으로 방에 체크인할 수 있어야 합니다."""
        # Given: COMPLETED 상태 티켓과 방
        assert sync_sample_completed_ticket.status == TicketStatus.COMPLETED
        room = _create_room_entity(sync_sample_room)

        # When
        room_stay = room_stay_sync_service.assign_room(sync_sample_completed_ticket, room)

        # Then
        assert room_stay is not None
        assert str(room_stay.user_id.value) == str(sync_sample_completed_ticket.user_id.value)
        assert str(room_stay.city_id.value) == str(sync_sample_completed_ticket.city_snapshot.city_id.value)
        assert str(room_stay.room_id.value) == str(sync_sample_room.room_id)
        assert str(room_stay.ticket_id.value) == str(sync_sample_completed_ticket.ticket_id.value)
        assert room_stay.status == RoomStayStatus.CHECKED_IN
        assert room_stay.extension_count == 0
        assert room_stay.actual_check_out_at is None

    def test_assign_room_sets_scheduled_check_out_at(
        self,
        room_stay_sync_service: RoomStaySyncService,
        sync_sample_completed_ticket: Ticket,
        sync_sample_room: RoomModel,
    ):
        """체크인 시 예정 체크아웃 시간이 24시간 후로 설정되어야 합니다."""
        # Given
        room = _create_room_entity(sync_sample_room)

        # When
        room_stay = room_stay_sync_service.assign_room(sync_sample_completed_ticket, room)

        # Then: 체크아웃 시간은 체크인 시간 + 24시간
        expected_duration = timedelta(hours=RoomStaySyncService.ROOM_STAY_DURATION_IN_HOUR)
        actual_duration = room_stay.scheduled_check_out_at - room_stay.check_in_at
        # 약간의 오차 허용 (테스트 실행 시간)
        assert abs(actual_duration - expected_duration) < timedelta(seconds=1)

    def test_assign_room_raises_error_when_ticket_not_completed(
        self,
        room_stay_sync_service: RoomStaySyncService,
        sync_sample_boarding_ticket: Ticket,
        sync_sample_room: RoomModel,
    ):
        """COMPLETED가 아닌 티켓으로 체크인하면 에러가 발생해야 합니다."""
        # Given: BOARDING 상태 티켓
        assert sync_sample_boarding_ticket.status == TicketStatus.BOARDING
        room = _create_room_entity(sync_sample_room)

        # When/Then
        with pytest.raises(InvalidTicketStatusError):
            room_stay_sync_service.assign_room(sync_sample_boarding_ticket, room)

    def test_assign_room_creates_unique_room_stay(
        self,
        room_stay_sync_service: RoomStaySyncService,
        sync_sample_completed_ticket: Ticket,
        sync_sample_room: RoomModel,
        sync_sample_guest_house: GuestHouseModel,
    ):
        """각 체크인은 고유한 room_stay_id를 가져야 합니다."""
        # Given
        room = _create_room_entity(sync_sample_room)

        # When
        room_stay = room_stay_sync_service.assign_room(sync_sample_completed_ticket, room)

        # Then: room_stay_id가 생성됨
        assert room_stay.room_stay_id is not None
        assert str(room_stay.guest_house_id.value) == str(sync_sample_guest_house.guest_house_id)
