"""Diary API E2E Tests - 모든 엣지 케이스 포함"""

from datetime import datetime

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.core.settings import get_settings
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.city_model import CityModel


@pytest_asyncio.fixture
async def sample_city(test_session: AsyncSession) -> CityModel:
    """테스트용 도시 데이터 생성"""
    city = CityModel(
        city_id=Id().value,
        name="세렌시아",
        theme="관계의 도시",
        description="관계에 대해 생각하는 도시",
        image_url="https://example.com/serencia.jpg",
        base_cost_points=100,
        base_duration_hours=1,
        is_active=True,
        display_order=1,
        created_at=datetime.now(get_settings().timezone),
        updated_at=datetime.now(get_settings().timezone),
    )
    test_session.add(city)
    await test_session.commit()
    await test_session.refresh(city)
    return city


@pytest.mark.asyncio
class TestDiaryAPICreate:
    """POST /api/v1/diaries - 일기 작성 API 테스트"""

    async def test_create_diary_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """일기 작성 성공 (모든 필드 포함)"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        payload = {
            "content": "오늘은 좋은 하루였다.",
            "mood": "😊",
            "title": "행복한 하루",
        }

        # When
        response = await client.post(
            "/api/v1/diaries",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["content"] == "오늘은 좋은 하루였다."
        assert data["mood"] == "😊"
        assert data["title"] == "행복한 하루"
        assert data["has_earned_points"] is True
        assert "diary_id" in data
        assert "diary_date" in data

    async def test_create_diary_success_minimal(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """일기 작성 성공 (필수 필드만)"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        payload = {
            "content": "짧은 일기",
            "mood": "😐",
        }

        # When
        response = await client.post(
            "/api/v1/diaries",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["content"] == "짧은 일기"
        assert data["mood"] == "😐"
        assert data["title"] is None
        assert data["city_id"] is None

    async def test_create_diary_duplicate(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """같은 날짜 중복 작성 시 409 Conflict"""
        # Given: 사용자 생성 및 오늘 일기 작성
        await client.post("/api/v1/users/me", headers=auth_headers)

        payload = {"content": "첫 번째 일기", "mood": "😊"}
        await client.post("/api/v1/diaries", json=payload, headers=auth_headers)

        # When: 같은 날짜에 다시 작성
        response = await client.post("/api/v1/diaries", json=payload, headers=auth_headers)

        # Then
        assert response.status_code == 409
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data

    async def test_create_diary_missing_content(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """필수 필드 content 누락 시 422 Validation Error"""
        # Given
        payload = {
            "mood": "😊",
        }

        # When
        response = await client.post(
            "/api/v1/diaries",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 422

    async def test_create_diary_missing_mood(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """필수 필드 mood 누락 시 422 Validation Error"""
        # Given
        payload = {
            "content": "내용만 있음",
        }

        # When
        response = await client.post(
            "/api/v1/diaries",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 422

    async def test_create_diary_empty_content(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """빈 문자열 content는 422 Validation Error (min_length=1)"""
        # Given
        payload = {
            "content": "",
            "mood": "😊",
        }

        # When
        response = await client.post(
            "/api/v1/diaries",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 422

    async def test_create_diary_content_too_long(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """content가 500자 초과 시 422 Validation Error"""
        # Given
        payload = {
            "content": "a" * 501,  # 501자
            "mood": "😊",
        }

        # When
        response = await client.post(
            "/api/v1/diaries",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 422

    async def test_create_diary_content_max_length_valid(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """content가 정확히 500자인 경우 성공"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        payload = {
            "content": "a" * 500,  # 정확히 500자
            "mood": "😊",
        }

        # When
        response = await client.post(
            "/api/v1/diaries",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 201

    async def test_create_diary_title_too_long(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """title이 100자 초과 시 422 Validation Error"""
        # Given
        payload = {
            "content": "내용",
            "mood": "😊",
            "title": "a" * 101,  # 101자
        }

        # When
        response = await client.post(
            "/api/v1/diaries",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 422

    async def test_create_diary_title_max_length_valid(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """title이 정확히 100자인 경우 성공"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        payload = {
            "content": "내용",
            "mood": "😊",
            "title": "a" * 100,  # 정확히 100자
        }

        # When
        response = await client.post(
            "/api/v1/diaries",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 201

    async def test_create_diary_invalid_city_id_format(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """잘못된 UUID 형식의 city_id로 요청 시 400 또는 422"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        payload = {
            "content": "내용",
            "mood": "😊",
            "city_id": "invalid-uuid-format",
        }

        # When
        response = await client.post(
            "/api/v1/diaries",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code in [400, 422]

    async def test_create_diary_with_valid_city_id(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
    ):
        """유효한 UUID 형식의 city_id로 요청 시 성공"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        payload = {
            "content": "도시 관련 일기",
            "mood": "😊",
            "city_id": sample_city.city_id.hex,
        }

        # When
        response = await client.post(
            "/api/v1/diaries",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["city_id"] == sample_city.city_id.hex


@pytest.mark.asyncio
class TestDiaryAPIGetById:
    """GET /api/v1/diaries/{diary_id} - 일기 상세 조회 API 테스트"""

    async def test_get_diary_by_id_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """일기 상세 조회 성공"""
        # Given: 사용자 생성 및 일기 작성
        await client.post("/api/v1/users/me", headers=auth_headers)

        create_response = await client.post(
            "/api/v1/diaries",
            json={"content": "테스트", "mood": "😊"},
            headers=auth_headers,
        )
        diary_id = create_response.json()["data"]["diary_id"]

        # When: 일기 조회
        response = await client.get(
            f"/api/v1/diaries/{diary_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["diary_id"] == diary_id
        assert data["content"] == "테스트"
        assert data["mood"] == "😊"

    async def test_get_diary_by_id_forbidden(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        auth_headers_factory,
    ):
        """다른 사용자의 일기 조회 시 403 Forbidden"""
        # Given: 사용자 A 생성 및 일기 작성
        await client.post("/api/v1/users/me", headers=auth_headers)

        create_response = await client.post(
            "/api/v1/diaries",
            json={"content": "사용자A 일기", "mood": "😊"},
            headers=auth_headers,
        )
        diary_id = create_response.json()["data"]["diary_id"]

        # Given: 사용자 B 생성
        other_user_headers = auth_headers_factory(
            provider="email",
            provider_user_id="other-user-id-456",
            email="other@example.com",
        )
        await client.post("/api/v1/users/me", headers=other_user_headers)

        # When: 사용자 B가 조회 시도
        response = await client.get(
            f"/api/v1/diaries/{diary_id}",
            headers=other_user_headers,
        )

        # Then
        assert response.status_code == 403

    async def test_get_diary_by_id_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """존재하지 않는 diary_id 조회 시 404 Not Found"""
        # Given: 존재하지 않는 UUID
        non_existent_id = "123e4567-e89b-12d3-a456-426614174999"

        # When
        response = await client.get(
            f"/api/v1/diaries/{non_existent_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 404

    async def test_get_diary_by_id_invalid_uuid_format(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """잘못된 UUID 형식으로 조회 시 400 또는 422"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        invalid_id = "invalid-uuid"

        # When
        response = await client.get(
            f"/api/v1/diaries/{invalid_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
class TestDiaryAPIGetList:
    """GET /api/v1/diaries - 일기 목록 조회 API 테스트"""

    async def test_get_diaries_list_default(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """일기 목록 조회 (기본값)"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When: 일기 목록 조회
        response = await client.get(
            "/api/v1/diaries",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "diaries" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data
        assert isinstance(data["diaries"], list)
        assert data["offset"] == 0
        assert data["limit"] == 20  # 기본값

    async def test_get_diaries_list_with_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """일기 목록 조회 (페이지네이션 파라미터)"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When: offset=5, limit=10으로 조회
        response = await client.get(
            "/api/v1/diaries?offset=5&limit=10",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 5
        assert data["limit"] == 10

    async def test_get_diaries_list_empty(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """일기가 없는 경우 빈 목록 반환"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When: 새 사용자가 일기 목록 조회
        response = await client.get(
            "/api/v1/diaries",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["diaries"]) == 0

    async def test_get_diaries_list_invalid_offset(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """음수 offset 시 400 또는 422"""
        # When
        response = await client.get(
            "/api/v1/diaries?offset=-1",
            headers=auth_headers,
        )

        # Then
        assert response.status_code in [400, 422]

    async def test_get_diaries_list_invalid_limit(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """음수 또는 0 limit 시 400 또는 422"""
        # When
        response = await client.get(
            "/api/v1/diaries?limit=0",
            headers=auth_headers,
        )

        # Then
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
class TestDiaryAPIGetToday:
    """GET /api/v1/diaries/today - 오늘 일기 조회 API 테스트"""

    async def test_get_today_diary_exists(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """오늘 일기가 있는 경우 조회 성공"""
        # Given: 사용자 생성 및 오늘 일기 작성
        await client.post("/api/v1/users/me", headers=auth_headers)

        await client.post(
            "/api/v1/diaries",
            json={"content": "오늘 일기", "mood": "😊"},
            headers=auth_headers,
        )

        # When: 오늘 일기 조회
        response = await client.get(
            "/api/v1/diaries/today",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()["data"]
        assert data is not None
        assert data["content"] == "오늘 일기"

    async def test_get_today_diary_not_exists(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """오늘 일기가 없는 경우 200 with null 또는 204"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When: 오늘 일기 조회 (작성 전)
        response = await client.get(
            "/api/v1/diaries/today",
            headers=auth_headers,
        )

        # Then: 200 with null data 또는 204 No Content
        assert response.status_code in [200, 204]
        if response.status_code == 200:
            data = response.json()["data"]
            assert data is None


@pytest.mark.asyncio
class TestDiaryAPIUnauthorized:
    """인증 관련 테스트"""

    async def test_create_diary_unauthorized(
        self,
        client: AsyncClient,
    ):
        """인증 없이 일기 작성 시 403"""
        # When
        response = await client.post(
            "/api/v1/diaries",
            json={"content": "내용", "mood": "😊"},
        )

        # Then
        assert response.status_code == 403

    async def test_get_diaries_unauthorized(
        self,
        client: AsyncClient,
    ):
        """인증 없이 일기 목록 조회 시 403"""
        # When
        response = await client.get("/api/v1/diaries")

        # Then
        assert response.status_code == 403

    async def test_get_diary_by_id_unauthorized(
        self,
        client: AsyncClient,
    ):
        """인증 없이 일기 상세 조회 시 403"""
        # When
        response = await client.get(
            "/api/v1/diaries/123e4567-e89b-12d3-a456-426614174000"
        )

        # Then
        assert response.status_code == 403

    async def test_get_today_diary_unauthorized(
        self,
        client: AsyncClient,
    ):
        """인증 없이 오늘 일기 조회 시 403"""
        # When
        response = await client.get("/api/v1/diaries/today")

        # Then
        assert response.status_code == 403
