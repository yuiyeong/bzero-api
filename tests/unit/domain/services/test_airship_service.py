"""AirshipService 단위 테스트"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from bzero.domain.entities.airship import Airship
from bzero.domain.repositories.airship import AirshipRepository
from bzero.domain.services.airship import AirshipService
from bzero.domain.value_objects import Id


@pytest.fixture
def mock_airship_repository() -> MagicMock:
    """Mock AirshipRepository"""
    return MagicMock(spec=AirshipRepository)


@pytest.fixture
def airship_service(mock_airship_repository: MagicMock) -> AirshipService:
    """AirshipService with mocked repository"""
    return AirshipService(mock_airship_repository)


@pytest.fixture
def sample_airships() -> list[Airship]:
    """샘플 비행선 목록"""
    now = datetime.now()
    return [
        Airship(
            airship_id=Id(),
            name="일반 비행선",
            description="편안하고 여유로운 여행을 원하는 여행자를 위한 비행선",
            image_url="https://example.com/normal.jpg",
            cost_factor=1,
            duration_factor=1,
            display_order=1,
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        Airship(
            airship_id=Id(),
            name="쾌속 비행선",
            description="빠른 이동을 원하는 여행자를 위한 비행선",
            image_url="https://example.com/fast.jpg",
            cost_factor=2,
            duration_factor=1,
            display_order=2,
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
    ]


class TestAirshipServiceGetAvailableAirships:
    """get_available_airships 메서드 테스트"""

    async def test_get_available_airships_returns_active_airships(
        self,
        airship_service: AirshipService,
        mock_airship_repository: MagicMock,
        sample_airships: list[Airship],
    ):
        """활성화된 비행선 목록을 반환한다"""
        # Given
        mock_airship_repository.find_all_by_active_state = AsyncMock(return_value=sample_airships)
        mock_airship_repository.count_by = AsyncMock(return_value=2)

        # When
        airships, total = await airship_service.get_available_airships()

        # Then
        assert len(airships) == 2
        assert airships[0].name == "일반 비행선"
        assert airships[0].is_active is True
        assert airships[1].name == "쾌속 비행선"
        assert airships[1].cost_factor == 2
        assert total == 2
        mock_airship_repository.find_all_by_active_state.assert_called_once_with(is_active=True, limit=100, offset=0)
        mock_airship_repository.count_by.assert_called_once_with(is_active=True)

    async def test_get_available_airships_with_pagination(
        self,
        airship_service: AirshipService,
        mock_airship_repository: MagicMock,
        sample_airships: list[Airship],
    ):
        """pagination 파라미터로 비행선 목록을 조회한다"""
        # Given
        mock_airship_repository.find_all_by_active_state = AsyncMock(return_value=sample_airships[:1])
        mock_airship_repository.count_by = AsyncMock(return_value=2)

        # When
        airships, total = await airship_service.get_available_airships(offset=0, limit=1)

        # Then
        assert len(airships) == 1
        assert airships[0].name == "일반 비행선"
        assert total == 2
        mock_airship_repository.find_all_by_active_state.assert_called_once_with(is_active=True, limit=1, offset=0)
        mock_airship_repository.count_by.assert_called_once_with(is_active=True)

    async def test_get_available_airships_with_offset(
        self,
        airship_service: AirshipService,
        mock_airship_repository: MagicMock,
        sample_airships: list[Airship],
    ):
        """offset 파라미터로 시작 위치를 지정할 수 있다"""
        # Given
        mock_airship_repository.find_all_by_active_state = AsyncMock(return_value=sample_airships[1:])
        mock_airship_repository.count_by = AsyncMock(return_value=2)

        # When
        airships, total = await airship_service.get_available_airships(offset=1, limit=10)

        # Then
        assert len(airships) == 1
        assert airships[0].name == "쾌속 비행선"
        assert total == 2
        mock_airship_repository.find_all_by_active_state.assert_called_once_with(is_active=True, limit=10, offset=1)

    async def test_get_available_airships_returns_empty_list_when_no_airships(
        self,
        airship_service: AirshipService,
        mock_airship_repository: MagicMock,
    ):
        """활성화된 비행선이 없을 때 빈 리스트를 반환한다"""
        # Given
        mock_airship_repository.find_all_by_active_state = AsyncMock(return_value=[])
        mock_airship_repository.count_by = AsyncMock(return_value=0)

        # When
        airships, total = await airship_service.get_available_airships()

        # Then
        assert airships == []
        assert total == 0
        mock_airship_repository.find_all_by_active_state.assert_called_once_with(is_active=True, limit=100, offset=0)
        mock_airship_repository.count_by.assert_called_once_with(is_active=True)

    async def test_get_available_airships_filters_inactive_airships(
        self,
        airship_service: AirshipService,
        mock_airship_repository: MagicMock,
        sample_airships: list[Airship],
    ):
        """비활성화된 비행선은 필터링된다"""
        # Given: 활성화된 비행선만 반환하도록 설정
        active_airships = [a for a in sample_airships if a.is_active]  # 모두 활성화된 상태
        mock_airship_repository.find_all_by_active_state = AsyncMock(return_value=active_airships)
        mock_airship_repository.count_by = AsyncMock(return_value=len(active_airships))

        # When
        airships, _ = await airship_service.get_available_airships()

        # Then: is_active=True로 필터링하여 조회
        assert all(airship.is_active for airship in airships)
        mock_airship_repository.find_all_by_active_state.assert_called_once_with(is_active=True, limit=100, offset=0)
