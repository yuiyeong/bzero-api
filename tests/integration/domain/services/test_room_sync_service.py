from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.orm import Session
from uuid_utils import uuid7

from bzero.domain.entities.room import Room
from bzero.domain.errors import InvalidRoomStatusError
from bzero.domain.services.room import RoomSyncService
from bzero.domain.value_objects import GuestHouseType, Id
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.room_model import RoomModel
from bzero.infrastructure.repositories.room import SqlAlchemyRoomSyncRepository


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone"""
    return ZoneInfo("Asia/Seoul")


@pytest.fixture
def room_sync_service(test_sync_session: Session, timezone: ZoneInfo) -> RoomSyncService:
    """RoomSyncService fixture를 생성합니다."""
    room_repository = SqlAlchemyRoomSyncRepository(test_sync_session)
    return RoomSyncService(room_repository, timezone)


@pytest.fixture
def sync_sample_city(test_sync_session: Session) -> CityModel:
    """테스트용 샘플 도시 데이터를 생성합니다."""
    now = datetime.now()
    city_model = CityModel(
        city_id=str(uuid7()),
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
    test_sync_session.add(city_model)
    test_sync_session.flush()
    return city_model


@pytest.fixture
def sync_sample_guest_house(test_sync_session: Session, sync_sample_city: CityModel) -> GuestHouseModel:
    """테스트용 샘플 게스트하우스 데이터를 생성합니다."""
    now = datetime.now()
    guest_house_model = GuestHouseModel(
        guest_house_id=str(uuid7()),
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
def sync_sample_available_room(test_sync_session: Session, sync_sample_guest_house: GuestHouseModel) -> RoomModel:
    """테스트용 여유 있는 방 데이터를 생성합니다."""
    now = datetime.now()
    room_model = RoomModel(
        room_id=str(uuid7()),
        guest_house_id=sync_sample_guest_house.guest_house_id,
        max_capacity=6,
        current_capacity=3,  # 3명 체류 중 (여유 있음)
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(room_model)
    test_sync_session.flush()
    return room_model


@pytest.fixture
def sync_sample_full_room(test_sync_session: Session, sync_sample_guest_house: GuestHouseModel) -> RoomModel:
    """테스트용 만원인 방 데이터를 생성합니다."""
    now = datetime.now()
    room_model = RoomModel(
        room_id=str(uuid7()),
        guest_house_id=sync_sample_guest_house.guest_house_id,
        max_capacity=6,
        current_capacity=6,  # 만원
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(room_model)
    test_sync_session.flush()
    return room_model


class TestRoomSyncServiceGetOrCreateRoomForUpdate:
    """get_or_create_room_for_update 메서드 통합 테스트"""

    def test_get_existing_available_room(
        self,
        room_sync_service: RoomSyncService,
        sync_sample_guest_house: GuestHouseModel,
        sync_sample_available_room: RoomModel,
    ):
        """여유 있는 기존 방이 있으면 해당 방을 반환해야 합니다."""
        # Given
        guest_house_id = Id(str(sync_sample_guest_house.guest_house_id))

        # When
        room = room_sync_service.get_or_create_room_for_update(guest_house_id)

        # Then
        assert room is not None
        assert str(room.room_id.value) == str(sync_sample_available_room.room_id)
        assert room.current_capacity == 3
        assert room.is_full is False

    def test_create_new_room_when_no_available(
        self,
        room_sync_service: RoomSyncService,
        sync_sample_guest_house: GuestHouseModel,
        sync_sample_full_room: RoomModel,
    ):
        """여유 있는 방이 없으면 새 방을 생성해야 합니다."""
        # Given: 기존 방은 만원 상태
        guest_house_id = Id(str(sync_sample_guest_house.guest_house_id))

        # When
        room = room_sync_service.get_or_create_room_for_update(guest_house_id)

        # Then: 새 방이 생성됨
        assert room is not None
        assert str(room.room_id.value) != str(sync_sample_full_room.room_id)
        assert room.current_capacity == 0  # 새 방은 비어있음
        assert room.max_capacity == RoomSyncService.MAX_CAPACITY

    def test_create_new_room_when_no_rooms_exist(
        self,
        room_sync_service: RoomSyncService,
        sync_sample_guest_house: GuestHouseModel,
    ):
        """방이 전혀 없으면 새 방을 생성해야 합니다."""
        # Given: 게스트하우스에 방이 없음
        guest_house_id = Id(str(sync_sample_guest_house.guest_house_id))

        # When
        room = room_sync_service.get_or_create_room_for_update(guest_house_id)

        # Then: 새 방이 생성됨
        assert room is not None
        assert str(room.guest_house_id.value) == str(sync_sample_guest_house.guest_house_id)
        assert room.current_capacity == 0
        assert room.max_capacity == 6


class TestRoomSyncServiceOccupyRoom:
    """occupy_room 메서드 통합 테스트"""

    def test_occupy_room_success(
        self,
        room_sync_service: RoomSyncService,
        sync_sample_guest_house: GuestHouseModel,
        sync_sample_available_room: RoomModel,
        test_sync_session: Session,
    ):
        """방에 여행자를 배정할 수 있어야 합니다."""
        # Given: 여유 있는 방
        room = Room(
            room_id=Id(str(sync_sample_available_room.room_id)),
            guest_house_id=Id(str(sync_sample_available_room.guest_house_id)),
            max_capacity=sync_sample_available_room.max_capacity,
            current_capacity=sync_sample_available_room.current_capacity,
            created_at=sync_sample_available_room.created_at,
            updated_at=sync_sample_available_room.updated_at,
        )
        initial_capacity = room.current_capacity

        # When
        updated_room = room_sync_service.occupy_room(room)

        # Then
        assert updated_room.current_capacity == initial_capacity + 1

    def test_occupy_room_raises_error_when_full(
        self,
        room_sync_service: RoomSyncService,
        sync_sample_full_room: RoomModel,
    ):
        """만원인 방에 여행자를 배정하면 에러가 발생해야 합니다."""
        # Given: 만원인 방
        full_room = Room(
            room_id=Id(str(sync_sample_full_room.room_id)),
            guest_house_id=Id(str(sync_sample_full_room.guest_house_id)),
            max_capacity=sync_sample_full_room.max_capacity,
            current_capacity=sync_sample_full_room.current_capacity,
            created_at=sync_sample_full_room.created_at,
            updated_at=sync_sample_full_room.updated_at,
        )

        # When/Then
        with pytest.raises(InvalidRoomStatusError):
            room_sync_service.occupy_room(full_room)

    def test_occupy_room_up_to_full(
        self,
        room_sync_service: RoomSyncService,
        sync_sample_guest_house: GuestHouseModel,
        test_sync_session: Session,
    ):
        """방에 최대 인원까지 여행자를 배정할 수 있어야 합니다."""
        # Given: 5명 체류 중인 방
        now = datetime.now()
        room_model = RoomModel(
            room_id=str(uuid7()),
            guest_house_id=sync_sample_guest_house.guest_house_id,
            max_capacity=6,
            current_capacity=5,
            created_at=now,
            updated_at=now,
        )
        test_sync_session.add(room_model)
        test_sync_session.flush()

        room = Room(
            room_id=Id(str(room_model.room_id)),
            guest_house_id=Id(str(room_model.guest_house_id)),
            max_capacity=room_model.max_capacity,
            current_capacity=room_model.current_capacity,
            created_at=room_model.created_at,
            updated_at=room_model.updated_at,
        )

        # When: 마지막 1명 배정
        updated_room = room_sync_service.occupy_room(room)

        # Then: 만원이 됨
        assert updated_room.current_capacity == 6
        assert updated_room.is_full is True
