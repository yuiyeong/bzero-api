"""City API E2E 테스트"""

from collections.abc import AsyncIterator
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.core.database import get_async_db_session
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.city_model import CityModel
from bzero.main import create_app


@pytest_asyncio.fixture
async def client(test_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """테스트용 HTTP 클라이언트를 생성합니다."""
    app = create_app()

    # DB 세션을 테스트 세션으로 오버라이드
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield test_session

    app.dependency_overrides[get_async_db_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def sample_cities(test_session: AsyncSession) -> list[CityModel]:
    """테스트용 도시 데이터 생성"""
    cities = [
        CityModel(
            city_id=Id().value,
            name="세렌시아",
            theme="관계의 도시",
            description="관계에 대해 생각하는 도시",
            image_url="https://example.com/serencia.jpg",
            is_active=True,
            display_order=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        CityModel(
            city_id=Id().value,
            name="플로라",
            theme="성장의 도시",
            description="성장에 대해 생각하는 도시",
            image_url="https://example.com/flora.jpg",
            is_active=True,
            display_order=2,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        CityModel(
            city_id=Id().value,
            name="비활성 도시",
            theme="테스트 도시",
            description="비활성 테스트 도시",
            image_url=None,
            is_active=False,
            display_order=3,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
    ]

    test_session.add_all(cities)
    await test_session.commit()

    for city in cities:
        await test_session.refresh(city)

    return cities


class TestGetActiveCities:
    """GET /cities 테스트"""

    async def test_get_active_cities_success(
        self, client: AsyncClient, sample_cities: list[CityModel]
    ):
        """활성 도시 목록 조회 성공"""
        # When
        response = await client.get("/cities")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        cities = data["data"]

        # 활성화된 도시만 반환 (2개)
        assert len(cities) == 2
        assert all(city["is_active"] is True for city in cities)

        # display_order 순서대로 정렬 확인
        assert cities[0]["name"] == "세렌시아"
        assert cities[0]["display_order"] == 1
        assert cities[1]["name"] == "플로라"
        assert cities[1]["display_order"] == 2

        # 응답 필드 확인
        first_city = cities[0]
        assert "city_id" in first_city
        assert "name" in first_city
        assert "theme" in first_city
        assert "description" in first_city
        assert "image_url" in first_city
        assert "is_active" in first_city
        assert "display_order" in first_city
        assert "created_at" in first_city
        assert "updated_at" in first_city

    async def test_get_active_cities_empty_list_when_no_cities(
        self, client: AsyncClient
    ):
        """도시가 없을 때 빈 리스트 반환"""
        # When
        response = await client.get("/cities")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []


class TestGetCityById:
    """GET /cities/{city_id} 테스트"""

    async def test_get_city_by_id_success(
        self, client: AsyncClient, sample_cities: list[CityModel]
    ):
        """도시 상세 정보 조회 성공"""
        # Given
        city = sample_cities[0]
        city_id = city.city_id.hex

        # When
        response = await client.get(f"/cities/{city_id}")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        city_data = data["data"]

        assert city_data["city_id"] == city_id
        assert city_data["name"] == "세렌시아"
        assert city_data["theme"] == "관계의 도시"
        assert city_data["description"] == "관계에 대해 생각하는 도시"
        assert city_data["is_active"] is True
        assert city_data["display_order"] == 1

    async def test_get_city_by_id_returns_inactive_city(
        self, client: AsyncClient, sample_cities: list[CityModel]
    ):
        """비활성 도시도 ID로 조회 가능"""
        # Given
        inactive_city = sample_cities[2]
        city_id = inactive_city.city_id.hex

        # When
        response = await client.get(f"/cities/{city_id}")

        # Then
        assert response.status_code == 200
        data = response.json()
        city_data = data["data"]

        assert city_data["city_id"] == city_id
        assert city_data["name"] == "비활성 도시"
        assert city_data["is_active"] is False

    async def test_get_city_by_id_not_found(self, client: AsyncClient):
        """존재하지 않는 도시 ID로 조회 시 404"""
        # Given
        nonexistent_id = Id().value.hex

        # When
        response = await client.get(f"/cities/{nonexistent_id}")

        # Then
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "NOT_FOUND" in data["error"]["code"]

    async def test_get_city_by_id_invalid_uuid_format(self, client: AsyncClient):
        """잘못된 UUID 형식으로 조회 시 400 또는 404"""
        # Given
        invalid_id = "invalid-uuid-format"

        # When
        response = await client.get(f"/cities/{invalid_id}")

        # Then
        # UUID 파싱 실패로 400 또는 404 예상
        assert response.status_code in [400, 404, 422]
