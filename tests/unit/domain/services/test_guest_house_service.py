"""GuestHouseSyncService 단위 테스트"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.entities import GuestHouse
from bzero.domain.errors import NotFoundGuestHouseError
from bzero.domain.repositories.guest_house import GuestHouseSyncRepository
from bzero.domain.services.guest_house import GuestHouseSyncService
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.guesthouse import GuestHouseType


@pytest.fixture
def mock_guest_house_repository() -> MagicMock:
    """Mock GuestHouseSyncRepository"""
    return MagicMock(spec=GuestHouseSyncRepository)


@pytest.fixture
def guest_house_service(mock_guest_house_repository: MagicMock) -> GuestHouseSyncService:
    """GuestHouseSyncService with mocked repository"""
    return GuestHouseSyncService(mock_guest_house_repository)


@pytest.fixture
def sample_city_id() -> Id:
    """샘플 도시 ID"""
    return Id(uuid7())


@pytest.fixture
def sample_guest_house(sample_city_id: Id) -> GuestHouse:
    """샘플 게스트하우스"""
    now = datetime.now(get_settings().timezone)
    return GuestHouse.create(
        city_id=sample_city_id,
        name="세렌시아 혼합형 게스트하우스",
        description="편안한 대화를 위한 공간",
        image_url="https://example.com/guesthouse.jpg",
        is_active=True,
        guest_house_type=GuestHouseType.MIXED,
        created_at=now,
        updated_at=now,
    )


class TestGuestHouseSyncServiceGetGuestHouseInCity:
    """get_guest_house_in_city 메서드 테스트"""

    def test_get_guest_house_in_city_returns_first_guest_house(
        self,
        guest_house_service: GuestHouseSyncService,
        mock_guest_house_repository: MagicMock,
        sample_city_id: Id,
        sample_guest_house: GuestHouse,
    ):
        """게스트하우스가 있으면 해당 게스트하우스를 반환한다"""
        # Given
        mock_guest_house_repository.find_available_one_by_city_id = MagicMock(return_value=sample_guest_house)

        # When
        guest_house = guest_house_service.get_guest_house_in_city(sample_city_id)

        # Then
        assert guest_house == sample_guest_house
        assert guest_house.city_id == sample_city_id
        mock_guest_house_repository.find_available_one_by_city_id.assert_called_once_with(sample_city_id)

    def test_get_guest_house_in_city_raises_not_found_error(
        self,
        guest_house_service: GuestHouseSyncService,
        mock_guest_house_repository: MagicMock,
        sample_city_id: Id,
    ):
        """게스트하우스가 없으면 NotFoundGuestHouseError를 발생시킨다"""
        # Given
        mock_guest_house_repository.find_available_one_by_city_id = MagicMock(return_value=None)

        # When/Then
        with pytest.raises(NotFoundGuestHouseError):
            guest_house_service.get_guest_house_in_city(sample_city_id)

        mock_guest_house_repository.find_available_one_by_city_id.assert_called_once_with(sample_city_id)
