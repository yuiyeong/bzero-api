"""Airship UseCase 단위 테스트"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from bzero.application.use_cases.airships.get_available_airships import (
    GetAvailableAirshipsUseCase,
)
from bzero.domain.entities.airship import Airship
from bzero.domain.value_objects import Id


@pytest.fixture
def mock_airship_service():
    """Mock AirshipService fixture"""
    return AsyncMock()


@pytest.fixture
def sample_airship():
    """샘플 비행선 엔티티"""
    now = datetime.now(UTC)
    return Airship(
        airship_id=Id.from_hex("01936d9d7c6f70008000000000000001"),
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


@pytest.fixture
def sample_airships():
    """샘플 비행선 목록"""
    now = datetime.now(UTC)
    return [
        Airship(
            airship_id=Id.from_hex("01936d9d7c6f70008000000000000001"),
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
            airship_id=Id.from_hex("01936d9d7c6f70008000000000000002"),
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


class TestGetAvailableAirshipsUseCase:
    """GetAvailableAirshipsUseCase 테스트"""

    async def test_execute_returns_available_airships(self, mock_airship_service, sample_airships):
        """이용 가능한 비행선 목록을 반환한다"""
        # Given
        mock_airship_service.get_available_airships.return_value = (
            sample_airships,
            2,
        )
        use_case = GetAvailableAirshipsUseCase(mock_airship_service)

        # When
        result = await use_case.execute(offset=0, limit=20)

        # Then
        assert len(result.items) == 2
        assert result.items[0].name == "일반 비행선"
        assert result.items[0].is_active is True
        assert result.items[0].cost_factor == 1
        assert result.items[1].name == "쾌속 비행선"
        assert result.items[1].cost_factor == 2
        assert result.total == 2
        assert result.offset == 0
        assert result.limit == 20
        mock_airship_service.get_available_airships.assert_called_once_with(offset=0, limit=20)

    async def test_execute_with_pagination(self, mock_airship_service, sample_airships):
        """pagination 파라미터로 비행선 목록을 조회한다"""
        # Given
        mock_airship_service.get_available_airships.return_value = (
            sample_airships[:1],
            2,
        )
        use_case = GetAvailableAirshipsUseCase(mock_airship_service)

        # When
        result = await use_case.execute(offset=0, limit=1)

        # Then
        assert len(result.items) == 1
        assert result.items[0].name == "일반 비행선"
        assert result.total == 2
        assert result.offset == 0
        assert result.limit == 1
        mock_airship_service.get_available_airships.assert_called_once_with(offset=0, limit=1)

    async def test_execute_with_offset(self, mock_airship_service, sample_airships):
        """offset 파라미터로 시작 위치를 지정할 수 있다"""
        # Given
        mock_airship_service.get_available_airships.return_value = (
            sample_airships[1:],
            2,
        )
        use_case = GetAvailableAirshipsUseCase(mock_airship_service)

        # When
        result = await use_case.execute(offset=1, limit=20)

        # Then
        assert len(result.items) == 1
        assert result.items[0].name == "쾌속 비행선"
        assert result.total == 2
        assert result.offset == 1
        mock_airship_service.get_available_airships.assert_called_once_with(offset=1, limit=20)

    async def test_execute_returns_empty_list_when_no_airships(self, mock_airship_service):
        """이용 가능한 비행선이 없을 때 빈 리스트를 반환한다"""
        # Given
        mock_airship_service.get_available_airships.return_value = ([], 0)
        use_case = GetAvailableAirshipsUseCase(mock_airship_service)

        # When
        result = await use_case.execute(offset=0, limit=20)

        # Then
        assert result.items == []
        assert result.total == 0
        mock_airship_service.get_available_airships.assert_called_once_with(offset=0, limit=20)

    async def test_execute_converts_to_result_objects(self, mock_airship_service, sample_airships):
        """엔티티를 AirshipResult 객체로 변환한다"""
        # Given
        mock_airship_service.get_available_airships.return_value = (
            sample_airships,
            2,
        )
        use_case = GetAvailableAirshipsUseCase(mock_airship_service)

        # When
        result = await use_case.execute(offset=0, limit=20)

        # Then: AirshipResult 타입으로 변환됨
        assert result.items[0].airship_id == sample_airships[0].airship_id.value.hex
        assert result.items[0].name == sample_airships[0].name
        assert result.items[0].cost_factor == sample_airships[0].cost_factor
        assert result.items[1].airship_id == sample_airships[1].airship_id.value.hex
