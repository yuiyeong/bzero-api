"""Questionnaire API E2E Tests - 모든 엣지 케이스 포함"""

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
class TestQuestionnaireAPICreate:
    """POST /api/v1/questionnaires - 문답지 작성 API 테스트"""

    async def test_create_questionnaire_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
    ):
        """문답지 작성 성공"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        payload = {
            "city_id": sample_city.city_id.hex,
            "question_1_answer": "답변1",
            "question_2_answer": "답변2",
            "question_3_answer": "답변3",
        }

        # When
        response = await client.post(
            "/api/v1/questionnaires",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["city_id"] == sample_city.city_id.hex
        assert data["question_1_answer"] == "답변1"
        assert data["question_2_answer"] == "답변2"
        assert data["question_3_answer"] == "답변3"
        assert data["has_earned_points"] is True
        assert "questionnaire_id" in data
        assert "created_at" in data

    async def test_create_questionnaire_duplicate(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
    ):
        """같은 도시 중복 작성 시 409 Conflict"""
        # Given: 사용자 생성 및 도시 A에 문답지 작성
        await client.post("/api/v1/users/me", headers=auth_headers)

        payload = {
            "city_id": sample_city.city_id.hex,
            "question_1_answer": "답변1",
            "question_2_answer": "답변2",
            "question_3_answer": "답변3",
        }
        await client.post("/api/v1/questionnaires", json=payload, headers=auth_headers)

        # When: 같은 도시에 다시 작성
        response = await client.post("/api/v1/questionnaires", json=payload, headers=auth_headers)

        # Then
        assert response.status_code == 409
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data

    async def test_create_questionnaire_different_cities(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
        test_session: AsyncSession,
    ):
        """다른 도시에는 각각 문답지 작성 가능"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # Given: 두 번째 도시 생성
        city_2 = CityModel(
            city_id=Id().value,
            name="두 번째 도시",
            theme="테스트",
            description="테스트 도시",
            image_url=None,
            base_cost_points=100,
            base_duration_hours=1,
            is_active=True,
            display_order=2,
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
        )
        test_session.add(city_2)
        await test_session.commit()
        await test_session.refresh(city_2)

        payload_city_1 = {
            "city_id": sample_city.city_id.hex,
            "question_1_answer": "도시1 답변1",
            "question_2_answer": "도시1 답변2",
            "question_3_answer": "도시1 답변3",
        }
        payload_city_2 = {
            "city_id": city_2.city_id.hex,
            "question_1_answer": "도시2 답변1",
            "question_2_answer": "도시2 답변2",
            "question_3_answer": "도시2 답변3",
        }

        # When
        response_1 = await client.post("/api/v1/questionnaires", json=payload_city_1, headers=auth_headers)
        response_2 = await client.post("/api/v1/questionnaires", json=payload_city_2, headers=auth_headers)

        # Then
        assert response_1.status_code == 201
        assert response_2.status_code == 201

    async def test_create_questionnaire_missing_city_id(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """필수 필드 city_id 누락 시 422 Validation Error"""
        # Given
        payload = {
            "question_1_answer": "답변1",
            "question_2_answer": "답변2",
            "question_3_answer": "답변3",
        }

        # When
        response = await client.post(
            "/api/v1/questionnaires",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 422

    async def test_create_questionnaire_missing_question_1(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """필수 필드 question_1_answer 누락 시 422"""
        # Given
        payload = {
            "city_id": "123e4567-e89b-12d3-a456-426614174000",
            "question_2_answer": "답변2",
            "question_3_answer": "답변3",
        }

        # When
        response = await client.post(
            "/api/v1/questionnaires",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 422

    async def test_create_questionnaire_missing_question_2(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """필수 필드 question_2_answer 누락 시 422"""
        # Given
        payload = {
            "city_id": "123e4567-e89b-12d3-a456-426614174000",
            "question_1_answer": "답변1",
            "question_3_answer": "답변3",
        }

        # When
        response = await client.post(
            "/api/v1/questionnaires",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 422

    async def test_create_questionnaire_missing_question_3(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """필수 필드 question_3_answer 누락 시 422"""
        # Given
        payload = {
            "city_id": "123e4567-e89b-12d3-a456-426614174000",
            "question_1_answer": "답변1",
            "question_2_answer": "답변2",
        }

        # When
        response = await client.post(
            "/api/v1/questionnaires",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 422

    async def test_create_questionnaire_empty_question_1(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """빈 문자열 question_1_answer는 422 (min_length=1)"""
        # Given
        payload = {
            "city_id": "123e4567-e89b-12d3-a456-426614174000",
            "question_1_answer": "",
            "question_2_answer": "답변2",
            "question_3_answer": "답변3",
        }

        # When
        response = await client.post(
            "/api/v1/questionnaires",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 422

    async def test_create_questionnaire_empty_question_2(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """빈 문자열 question_2_answer는 422"""
        # Given
        payload = {
            "city_id": "123e4567-e89b-12d3-a456-426614174000",
            "question_1_answer": "답변1",
            "question_2_answer": "",
            "question_3_answer": "답변3",
        }

        # When
        response = await client.post(
            "/api/v1/questionnaires",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 422

    async def test_create_questionnaire_empty_question_3(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """빈 문자열 question_3_answer는 422"""
        # Given
        payload = {
            "city_id": "123e4567-e89b-12d3-a456-426614174000",
            "question_1_answer": "답변1",
            "question_2_answer": "답변2",
            "question_3_answer": "",
        }

        # When
        response = await client.post(
            "/api/v1/questionnaires",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 422

    async def test_create_questionnaire_question_1_too_long(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """question_1_answer가 200자 초과 시 422"""
        # Given
        payload = {
            "city_id": "123e4567-e89b-12d3-a456-426614174000",
            "question_1_answer": "a" * 201,
            "question_2_answer": "답변2",
            "question_3_answer": "답변3",
        }

        # When
        response = await client.post(
            "/api/v1/questionnaires",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 422

    async def test_create_questionnaire_question_1_max_length_valid(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
    ):
        """question_1_answer가 정확히 200자인 경우 성공"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        payload = {
            "city_id": sample_city.city_id.hex,
            "question_1_answer": "a" * 200,
            "question_2_answer": "답변2",
            "question_3_answer": "답변3",
        }

        # When
        response = await client.post(
            "/api/v1/questionnaires",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 201

    async def test_create_questionnaire_question_2_too_long(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """question_2_answer가 200자 초과 시 422"""
        # Given
        payload = {
            "city_id": "123e4567-e89b-12d3-a456-426614174000",
            "question_1_answer": "답변1",
            "question_2_answer": "b" * 201,
            "question_3_answer": "답변3",
        }

        # When
        response = await client.post(
            "/api/v1/questionnaires",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 422

    async def test_create_questionnaire_question_3_too_long(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """question_3_answer가 200자 초과 시 422"""
        # Given
        payload = {
            "city_id": "123e4567-e89b-12d3-a456-426614174000",
            "question_1_answer": "답변1",
            "question_2_answer": "답변2",
            "question_3_answer": "c" * 201,
        }

        # When
        response = await client.post(
            "/api/v1/questionnaires",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 422

    async def test_create_questionnaire_invalid_city_id_format(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """잘못된 UUID 형식의 city_id로 요청 시 400 또는 422"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        payload = {
            "city_id": "invalid-uuid-format",
            "question_1_answer": "답변1",
            "question_2_answer": "답변2",
            "question_3_answer": "답변3",
        }

        # When
        response = await client.post(
            "/api/v1/questionnaires",
            json=payload,
            headers=auth_headers,
        )

        # Then
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
class TestQuestionnaireAPIGetById:
    """GET /api/v1/questionnaires/{questionnaire_id} - 문답지 상세 조회 API 테스트"""

    async def test_get_questionnaire_by_id_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
    ):
        """문답지 상세 조회 성공"""
        # Given: 사용자 생성 및 문답지 작성
        await client.post("/api/v1/users/me", headers=auth_headers)

        create_response = await client.post(
            "/api/v1/questionnaires",
            json={
                "city_id": sample_city.city_id.hex,
                "question_1_answer": "답변1",
                "question_2_answer": "답변2",
                "question_3_answer": "답변3",
            },
            headers=auth_headers,
        )
        questionnaire_id = create_response.json()["data"]["questionnaire_id"]

        # When: 문답지 조회
        response = await client.get(
            f"/api/v1/questionnaires/{questionnaire_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["questionnaire_id"] == questionnaire_id
        assert data["question_1_answer"] == "답변1"
        assert data["question_2_answer"] == "답변2"
        assert data["question_3_answer"] == "답변3"

    async def test_get_questionnaire_by_id_forbidden(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        auth_headers_factory,
        sample_city: CityModel,
    ):
        """다른 사용자의 문답지 조회 시 403 Forbidden"""
        # Given: 사용자 A 생성 및 문답지 작성
        await client.post("/api/v1/users/me", headers=auth_headers)

        create_response = await client.post(
            "/api/v1/questionnaires",
            json={
                "city_id": sample_city.city_id.hex,
                "question_1_answer": "답변1",
                "question_2_answer": "답변2",
                "question_3_answer": "답변3",
            },
            headers=auth_headers,
        )
        questionnaire_id = create_response.json()["data"]["questionnaire_id"]

        # Given: 사용자 B 생성
        other_user_headers = auth_headers_factory(
            provider="email",
            provider_user_id="other-user-id-789",
            email="other@example.com",
        )
        await client.post("/api/v1/users/me", headers=other_user_headers)

        # When: 사용자 B가 조회 시도
        response = await client.get(
            f"/api/v1/questionnaires/{questionnaire_id}",
            headers=other_user_headers,
        )

        # Then
        assert response.status_code == 403

    async def test_get_questionnaire_by_id_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """존재하지 않는 questionnaire_id 조회 시 404 Not Found"""
        # Given: 존재하지 않는 UUID
        non_existent_id = "123e4567-e89b-12d3-a456-426614174999"

        # When
        response = await client.get(
            f"/api/v1/questionnaires/{non_existent_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 404

    async def test_get_questionnaire_by_id_invalid_uuid_format(
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
            f"/api/v1/questionnaires/{invalid_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
class TestQuestionnaireAPIGetList:
    """GET /api/v1/questionnaires - 문답지 목록 조회 API 테스트"""

    async def test_get_questionnaires_list_default(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """문답지 목록 조회 (기본값)"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When: 문답지 목록 조회
        response = await client.get(
            "/api/v1/questionnaires",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "questionnaires" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data
        assert isinstance(data["questionnaires"], list)
        assert data["offset"] == 0
        assert data["limit"] == 20  # 기본값

    async def test_get_questionnaires_list_with_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """문답지 목록 조회 (페이지네이션 파라미터)"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When: offset=3, limit=5로 조회
        response = await client.get(
            "/api/v1/questionnaires?offset=3&limit=5",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 3
        assert data["limit"] == 5

    async def test_get_questionnaires_list_empty(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """문답지가 없는 경우 빈 목록 반환"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When: 새 사용자가 문답지 목록 조회
        response = await client.get(
            "/api/v1/questionnaires",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["questionnaires"]) == 0

    async def test_get_questionnaires_list_invalid_offset(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """음수 offset 시 400 또는 422"""
        # When
        response = await client.get(
            "/api/v1/questionnaires?offset=-1",
            headers=auth_headers,
        )

        # Then
        assert response.status_code in [400, 422]

    async def test_get_questionnaires_list_invalid_limit(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """음수 또는 0 limit 시 400 또는 422"""
        # When
        response = await client.get(
            "/api/v1/questionnaires?limit=0",
            headers=auth_headers,
        )

        # Then
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
class TestQuestionnaireAPIUnauthorized:
    """인증 관련 테스트"""

    async def test_create_questionnaire_unauthorized(
        self,
        client: AsyncClient,
    ):
        """인증 없이 문답지 작성 시 403"""
        # When
        response = await client.post(
            "/api/v1/questionnaires",
            json={
                "city_id": "123e4567-e89b-12d3-a456-426614174000",
                "question_1_answer": "답변1",
                "question_2_answer": "답변2",
                "question_3_answer": "답변3",
            },
        )

        # Then
        assert response.status_code == 403

    async def test_get_questionnaires_unauthorized(
        self,
        client: AsyncClient,
    ):
        """인증 없이 문답지 목록 조회 시 403"""
        # When
        response = await client.get("/api/v1/questionnaires")

        # Then
        assert response.status_code == 403

    async def test_get_questionnaire_by_id_unauthorized(
        self,
        client: AsyncClient,
    ):
        """인증 없이 문답지 상세 조회 시 403"""
        # When
        response = await client.get(
            "/api/v1/questionnaires/123e4567-e89b-12d3-a456-426614174000"
        )

        # Then
        assert response.status_code == 403
