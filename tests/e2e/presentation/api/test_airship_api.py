"""Airship API E2E 테스트"""

from datetime import datetime

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.core.settings import get_settings
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.airship_model import AirshipModel


@pytest_asyncio.fixture
async def sample_airships(test_session: AsyncSession) -> list[AirshipModel]:
    """테스트용 비행선 데이터 생성"""
    airships = [
        AirshipModel(
            airship_id=Id().value,
            name="일반 비행선",
            description="편안한 속도로 여행하는 일반 비행선입니다.",
            image_url="https://example.com/normal_airship.jpg",
            cost_factor=1,
            duration_factor=1,
            display_order=1,
            is_active=True,
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
        ),
        AirshipModel(
            airship_id=Id().value,
            name="쾌속 비행선",
            description="빠른 속도로 이동할 수 있는 쾌속 비행선입니다.",
            image_url="https://example.com/express_airship.jpg",
            cost_factor=2,
            duration_factor=1,
            display_order=2,
            is_active=True,
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
        ),
        AirshipModel(
            airship_id=Id().value,
            name="특급 비행선",
            description="가장 빠른 특급 비행선입니다.",
            image_url=None,
            cost_factor=3,
            duration_factor=1,
            display_order=3,
            is_active=True,
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
        ),
        AirshipModel(
            airship_id=Id().value,
            name="비활성 비행선",
            description="현재 운행하지 않는 비행선입니다.",
            image_url=None,
            cost_factor=1,
            duration_factor=1,
            display_order=4,
            is_active=False,
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
        ),
    ]

    test_session.add_all(airships)
    await test_session.commit()

    for airship in airships:
        await test_session.refresh(airship)

    return airships


class TestGetAvailableAirships:
    """GET /api/v1/airships 테스트"""

    async def test_get_available_airships_success(self, client: AsyncClient, sample_airships: list[AirshipModel]):
        """이용 가능한 비행선 목록 조회 성공"""
        # When
        response = await client.get("/api/v1/airships")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "list" in data
        assert "pagination" in data

        airships = data["list"]
        pagination = data["pagination"]

        # 활성화된 비행선만 반환 (3개)
        assert len(airships) == 3
        assert all(airship["name"] != "비활성 비행선" for airship in airships)

        # pagination 정보 확인
        assert pagination["total"] == 3
        assert pagination["offset"] == 0
        assert pagination["limit"] == 20

        # display_order 순서대로 정렬 확인 (이름으로 검증)
        assert airships[0]["name"] == "일반 비행선"
        assert airships[1]["name"] == "쾌속 비행선"
        assert airships[2]["name"] == "특급 비행선"

        # 응답 필드 확인
        first_airship = airships[0]
        assert "airship_id" in first_airship
        assert "name" in first_airship
        assert "description" in first_airship
        assert "image_url" in first_airship
        assert "created_at" in first_airship
        assert "updated_at" in first_airship

        # 첫 번째 비행선의 값 검증
        assert first_airship["name"] == "일반 비행선"
        assert first_airship["description"] == "편안한 속도로 여행하는 일반 비행선입니다."
        assert first_airship["image_url"] == "https://example.com/normal_airship.jpg"

    async def test_get_available_airships_with_pagination(
        self, client: AsyncClient, sample_airships: list[AirshipModel]
    ):
        """pagination 파라미터로 비행선 목록 조회"""
        # When
        response = await client.get("/api/v1/airships?offset=0&limit=1")

        # Then
        assert response.status_code == 200
        data = response.json()

        airships = data["list"]
        pagination = data["pagination"]

        # 1개만 반환
        assert len(airships) == 1
        assert airships[0]["name"] == "일반 비행선"

        # pagination 정보
        assert pagination["total"] == 3
        assert pagination["offset"] == 0
        assert pagination["limit"] == 1

    async def test_get_available_airships_with_offset(self, client: AsyncClient, sample_airships: list[AirshipModel]):
        """offset 파라미터로 두 번째 페이지 조회"""
        # When
        response = await client.get("/api/v1/airships?offset=1&limit=2")

        # Then
        assert response.status_code == 200
        data = response.json()

        airships = data["list"]
        pagination = data["pagination"]

        # 2개 반환 (두 번째, 세 번째 비행선)
        assert len(airships) == 2
        assert airships[0]["name"] == "쾌속 비행선"
        assert airships[1]["name"] == "특급 비행선"

        # pagination 정보
        assert pagination["total"] == 3
        assert pagination["offset"] == 1
        assert pagination["limit"] == 2

    async def test_get_available_airships_with_large_offset(
        self, client: AsyncClient, sample_airships: list[AirshipModel]
    ):
        """offset이 전체 개수보다 큰 경우 빈 리스트 반환"""
        # When
        response = await client.get("/api/v1/airships?offset=10&limit=20")

        # Then
        assert response.status_code == 200
        data = response.json()

        airships = data["list"]
        pagination = data["pagination"]

        # 빈 리스트 반환
        assert len(airships) == 0

        # pagination 정보는 정상적으로 반환
        assert pagination["total"] == 3
        assert pagination["offset"] == 10
        assert pagination["limit"] == 20

    async def test_get_available_airships_empty_list_when_no_airships(self, client: AsyncClient):
        """비행선이 없을 때 빈 리스트 반환"""
        # When
        response = await client.get("/api/v1/airships")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["list"] == []
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["offset"] == 0
        assert data["pagination"]["limit"] == 20

    async def test_get_available_airships_with_max_limit(
        self, client: AsyncClient, sample_airships: list[AirshipModel]
    ):
        """limit 최댓값(100) 파라미터로 조회"""
        # When
        response = await client.get("/api/v1/airships?offset=0&limit=100")

        # Then
        assert response.status_code == 200
        data = response.json()

        airships = data["list"]
        pagination = data["pagination"]

        # 활성 비행선 3개 모두 반환
        assert len(airships) == 3

        # pagination 정보
        assert pagination["total"] == 3
        assert pagination["offset"] == 0
        assert pagination["limit"] == 100

    async def test_get_available_airships_with_invalid_offset(self, client: AsyncClient):
        """음수 offset으로 조회 시 422 에러"""
        # When
        response = await client.get("/api/v1/airships?offset=-1&limit=20")

        # Then
        # FastAPI Query validation error
        assert response.status_code == 422

    async def test_get_available_airships_with_invalid_limit(self, client: AsyncClient):
        """잘못된 limit으로 조회 시 422 에러"""
        # When: limit이 0 이하인 경우
        response = await client.get("/api/v1/airships?offset=0&limit=0")

        # Then
        assert response.status_code == 422

    async def test_get_available_airships_with_limit_over_max(self, client: AsyncClient):
        """limit이 최댓값(100)을 초과하는 경우 422 에러"""
        # When
        response = await client.get("/api/v1/airships?offset=0&limit=101")

        # Then
        assert response.status_code == 422

    async def test_get_available_airships_excludes_inactive(
        self, client: AsyncClient, sample_airships: list[AirshipModel]
    ):
        """비활성화된 비행선은 목록에 포함되지 않음"""
        # When
        response = await client.get("/api/v1/airships")

        # Then
        assert response.status_code == 200
        data = response.json()
        airships = data["list"]

        # 비활성 비행선은 포함되지 않음
        assert len(airships) == 3
        airship_names = [airship["name"] for airship in airships]
        assert "비활성 비행선" not in airship_names
        assert "일반 비행선" in airship_names
        assert "쾌속 비행선" in airship_names
        assert "특급 비행선" in airship_names

    async def test_get_available_airships_respects_display_order(
        self, client: AsyncClient, sample_airships: list[AirshipModel]
    ):
        """비행선 목록이 display_order 순서대로 정렬되어 반환됨"""
        # When
        response = await client.get("/api/v1/airships")

        # Then
        assert response.status_code == 200
        data = response.json()
        airships = data["list"]

        # display_order 오름차순 확인 (이름으로 검증)
        assert len(airships) == 3
        assert airships[0]["name"] == "일반 비행선"
        assert airships[1]["name"] == "쾌속 비행선"
        assert airships[2]["name"] == "특급 비행선"
