"""City UseCase 단위 테스트"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from bzero.application.use_cases.cities.get_active_cities import (
    GetActiveCitiesUseCase,
)
from bzero.application.use_cases.cities.get_city_by_id import GetCityByIdUseCase
from bzero.domain.entities.city import City
from bzero.domain.errors import ErrorCode, NotFoundError
from bzero.domain.value_objects import Id


@pytest.fixture
def mock_city_service():
    """Mock CityService fixture"""
    return AsyncMock()


@pytest.fixture
def sample_city():
    """샘플 도시 엔티티"""
    now = datetime.now(timezone.utc)
    return City(
        city_id=Id.from_hex("01936d9d7c6f70008000000000000001"),
        name="세렌시아",
        theme="관계의 도시",
        description="관계에 대해 생각하는 도시",
        image_url="https://example.com/serencia.jpg",
        is_active=True,
        display_order=1,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_cities():
    """샘플 도시 목록"""
    now = datetime.now(timezone.utc)
    return [
        City(
            city_id=Id.from_hex("01936d9d7c6f70008000000000000001"),
            name="세렌시아",
            theme="관계의 도시",
            description="관계에 대해 생각하는 도시",
            image_url="https://example.com/serencia.jpg",
            is_active=True,
            display_order=1,
            created_at=now,
            updated_at=now,
        ),
        City(
            city_id=Id.from_hex("01936d9d7c6f70008000000000000002"),
            name="플로라",
            theme="성장의 도시",
            description="성장에 대해 생각하는 도시",
            image_url="https://example.com/flora.jpg",
            is_active=True,
            display_order=2,
            created_at=now,
            updated_at=now,
        ),
    ]


class TestGetActiveCitiesUseCase:
    """GetActiveCitiesUseCase 테스트"""

    async def test_execute_returns_active_cities(
        self, mock_city_service, sample_cities
    ):
        """활성 도시 목록을 반환한다"""
        # Given
        mock_city_service.get_active_cities.return_value = sample_cities
        use_case = GetActiveCitiesUseCase(mock_city_service)

        # When
        results = await use_case.execute()

        # Then
        assert len(results) == 2
        assert results[0].name == "세렌시아"
        assert results[0].is_active is True
        assert results[1].name == "플로라"
        assert results[1].display_order == 2
        mock_city_service.get_active_cities.assert_called_once()

    async def test_execute_returns_empty_list_when_no_cities(
        self, mock_city_service
    ):
        """활성 도시가 없을 때 빈 리스트를 반환한다"""
        # Given
        mock_city_service.get_active_cities.return_value = []
        use_case = GetActiveCitiesUseCase(mock_city_service)

        # When
        results = await use_case.execute()

        # Then
        assert results == []
        mock_city_service.get_active_cities.assert_called_once()


class TestGetCityByIdUseCase:
    """GetCityByIdUseCase 테스트"""

    async def test_execute_returns_city_when_found(
        self, mock_city_service, sample_city
    ):
        """도시 ID로 도시를 찾으면 반환한다"""
        # Given
        city_id = "01936d9d7c6f70008000000000000001"
        mock_city_service.get_city_by_id.return_value = sample_city
        use_case = GetCityByIdUseCase(mock_city_service)

        # When
        result = await use_case.execute(city_id)

        # Then
        assert result.city_id == sample_city.city_id.value.hex
        assert result.name == "세렌시아"
        assert result.theme == "관계의 도시"
        mock_city_service.get_city_by_id.assert_called_once()
        call_args = mock_city_service.get_city_by_id.call_args[0][0]
        assert call_args.value.hex == city_id

    async def test_execute_raises_not_found_error_when_city_not_exists(
        self, mock_city_service
    ):
        """도시를 찾을 수 없으면 NotFoundError를 발생시킨다"""
        # Given
        city_id = "01936d9d7c6f70008000000000000099"
        mock_city_service.get_city_by_id.side_effect = NotFoundError(ErrorCode.NOT_FOUND)
        use_case = GetCityByIdUseCase(mock_city_service)

        # When & Then
        with pytest.raises(NotFoundError):
            await use_case.execute(city_id)

        mock_city_service.get_city_by_id.assert_called_once()
