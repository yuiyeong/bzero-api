"""RoomSyncService 단위 테스트"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.entities import Room
from bzero.domain.repositories.room import RoomSyncRepository
from bzero.domain.services.room import RoomSyncService
from bzero.domain.value_objects import Id


@pytest.fixture
def mock_room_repository() -> MagicMock:
    """Mock RoomSyncRepository"""
    return MagicMock(spec=RoomSyncRepository)


@pytest.fixture
def room_service(mock_room_repository: MagicMock) -> RoomSyncService:
    """RoomSyncService with mocked repository"""
    timezone = get_settings().timezone
    return RoomSyncService(mock_room_repository, timezone)


@pytest.fixture
def sample_guesthouse_id() -> Id:
    """샘플 게스트하우스 ID"""
    return Id(uuid7())


@pytest.fixture
def sample_room(sample_guesthouse_id: Id) -> Room:
    """샘플 방 (정원 3명)"""
    now = datetime.now(get_settings().timezone)
    room = Room.create(
        guest_house_id=sample_guesthouse_id,
        max_capacity=6,
        created_at=now,
        updated_at=now,
    )
    # 현재 3명 체류 중
    room.current_capacity = 3
    return room


class TestRoomSyncServiceGetOrCreateRoomForUpdate:
    """get_or_create_room_for_update 메서드 테스트"""

    def test_get_or_create_room_for_update_returns_existing_room(
        self,
        room_service: RoomSyncService,
        mock_room_repository: MagicMock,
        sample_guesthouse_id: Id,
        sample_room: Room,
    ):
        """이용 가능한 방이 있으면 기존 방을 반환한다"""
        # Given
        assert sample_room.current_capacity < sample_room.max_capacity
        mock_room_repository.find_available_by_guest_house_id_for_update = MagicMock(return_value=[sample_room])

        # When
        room = room_service.get_or_create_room_for_update(sample_guesthouse_id)

        # Then
        assert room == sample_room
        assert room.guest_house_id == sample_guesthouse_id
        mock_room_repository.find_available_by_guest_house_id_for_update.assert_called_once_with(sample_guesthouse_id)
        mock_room_repository.create.assert_not_called()

    def test_get_or_create_room_for_update_creates_new_room(
        self,
        room_service: RoomSyncService,
        mock_room_repository: MagicMock,
        sample_guesthouse_id: Id,
    ):
        """이용 가능한 방이 없으면 새 방을 생성한다"""
        # Given
        mock_room_repository.find_available_by_guest_house_id_for_update = MagicMock(return_value=[])

        created_room = Room.create(
            guest_house_id=sample_guesthouse_id,
            max_capacity=6,
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
        )
        mock_room_repository.create = MagicMock(return_value=created_room)

        # When
        room = room_service.get_or_create_room_for_update(sample_guesthouse_id)

        # Then
        assert room.guest_house_id == sample_guesthouse_id
        assert room.max_capacity == RoomSyncService.MAX_CAPACITY
        assert room.current_capacity == 0
        mock_room_repository.find_available_by_guest_house_id_for_update.assert_called_once_with(sample_guesthouse_id)
        mock_room_repository.create.assert_called_once()

    def test_get_or_create_room_for_update_returns_first_available_room_when_multiple_exist(
        self,
        room_service: RoomSyncService,
        mock_room_repository: MagicMock,
        sample_guesthouse_id: Id,
    ):
        """여러 개의 이용 가능한 방이 있으면 첫 번째 방을 반환한다"""
        # Given
        now = datetime.now(get_settings().timezone)
        room1 = Room.create(
            guest_house_id=sample_guesthouse_id,
            max_capacity=6,
            created_at=now,
            updated_at=now,
        )
        room1.current_capacity = 2

        room2 = Room.create(
            guest_house_id=sample_guesthouse_id,
            max_capacity=6,
            created_at=now,
            updated_at=now,
        )
        room2.current_capacity = 4

        mock_room_repository.find_available_by_guest_house_id_for_update = MagicMock(return_value=[room1, room2])

        # When
        room = room_service.get_or_create_room_for_update(sample_guesthouse_id)

        # Then
        assert room == room1
        assert room.current_capacity == 2
        mock_room_repository.create.assert_not_called()
