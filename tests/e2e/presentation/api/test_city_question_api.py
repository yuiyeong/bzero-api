"""도시 질문 API E2E 테스트."""

from datetime import datetime

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.core.settings import get_settings
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.city_question_model import CityQuestionModel


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def sample_city(test_session: AsyncSession) -> CityModel:
    """테스트용 도시 데이터 생성."""
    now = datetime.now(get_settings().timezone)
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
        created_at=now,
        updated_at=now,
    )
    test_session.add(city)
    await test_session.commit()
    await test_session.refresh(city)
    return city


@pytest_asyncio.fixture
async def sample_city_question(
    test_session: AsyncSession,
    sample_city: CityModel,
) -> CityQuestionModel:
    """테스트용 도시 질문 데이터 생성."""
    now = datetime.now(get_settings().timezone)
    question = CityQuestionModel(
        city_question_id=Id().value,
        city_id=sample_city.city_id,
        question="오늘 가장 감사했던 순간은 언제인가요?",
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(question)
    await test_session.commit()
    await test_session.refresh(question)
    return question


@pytest_asyncio.fixture
async def sample_city_questions(
    test_session: AsyncSession,
    sample_city: CityModel,
) -> list[CityQuestionModel]:
    """테스트용 도시 질문 목록 생성."""
    now = datetime.now(get_settings().timezone)
    question_texts = [
        "오늘 가장 감사했던 순간은 언제인가요?",
        "최근에 누군가에게 받은 따뜻한 말이 있나요?",
        "오늘 하루 중 가장 기억에 남는 순간은?",
        "지금 이 순간 가장 편안하게 느껴지는 것은 무엇인가요?",
    ]

    questions: list[CityQuestionModel] = []
    for i, text in enumerate(question_texts):
        question = CityQuestionModel(
            city_question_id=Id().value,
            city_id=sample_city.city_id,
            question=text,
            display_order=i + 1,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        test_session.add(question)
        questions.append(question)

    await test_session.commit()
    for q in questions:
        await test_session.refresh(q)
    return questions


@pytest_asyncio.fixture
async def inactive_city_question(
    test_session: AsyncSession,
    sample_city: CityModel,
) -> CityQuestionModel:
    """비활성화된 도시 질문 데이터 생성."""
    now = datetime.now(get_settings().timezone)
    question = CityQuestionModel(
        city_question_id=Id().value,
        city_id=sample_city.city_id,
        question="비활성화된 질문입니다.",
        display_order=100,
        is_active=False,
        created_at=now,
        updated_at=now,
    )
    test_session.add(question)
    await test_session.commit()
    await test_session.refresh(question)
    return question


# =============================================================================
# Tests: GET /api/v1/city-questions
# =============================================================================


class TestGetCityQuestions:
    """GET /api/v1/city-questions 테스트."""

    async def test_get_city_questions_success(
        self,
        client: AsyncClient,
        sample_city: CityModel,
        sample_city_question: CityQuestionModel,
    ):
        """도시 질문 목록 조회 성공."""
        # When
        response = await client.get(
            f"/api/v1/city-questions?city_id={sample_city.city_id.hex}",
        )

        # Then
        assert response.status_code == 200
        data = response.json()

        assert "list" in data
        assert len(data["list"]) == 1

        question = data["list"][0]
        assert question["city_question_id"] == sample_city_question.city_question_id.hex
        assert question["city_id"] == sample_city.city_id.hex
        assert question["question"] == sample_city_question.question
        assert question["display_order"] == sample_city_question.display_order
        assert question["is_active"] is True
        assert "created_at" in question
        assert "updated_at" in question

    async def test_get_city_questions_multiple_questions(
        self,
        client: AsyncClient,
        sample_city: CityModel,
        sample_city_questions: list[CityQuestionModel],
    ):
        """여러 질문이 있을 때 목록 조회."""
        # When
        response = await client.get(
            f"/api/v1/city-questions?city_id={sample_city.city_id.hex}",
        )

        # Then
        assert response.status_code == 200
        data = response.json()

        assert len(data["list"]) == 4

    async def test_get_city_questions_ordered_by_display_order(
        self,
        client: AsyncClient,
        sample_city: CityModel,
        sample_city_questions: list[CityQuestionModel],
    ):
        """질문은 display_order 순으로 정렬됨."""
        # When
        response = await client.get(
            f"/api/v1/city-questions?city_id={sample_city.city_id.hex}",
        )

        # Then
        assert response.status_code == 200
        question_list = response.json()["list"]

        for i in range(len(question_list) - 1):
            assert question_list[i]["display_order"] < question_list[i + 1]["display_order"]

    async def test_get_city_questions_only_active(
        self,
        client: AsyncClient,
        sample_city: CityModel,
        sample_city_question: CityQuestionModel,
        inactive_city_question: CityQuestionModel,
    ):
        """비활성화된 질문은 조회되지 않음."""
        # When
        response = await client.get(
            f"/api/v1/city-questions?city_id={sample_city.city_id.hex}",
        )

        # Then
        assert response.status_code == 200
        data = response.json()

        # 활성화된 질문만 조회됨
        assert len(data["list"]) == 1
        assert data["list"][0]["city_question_id"] == sample_city_question.city_question_id.hex

    async def test_get_city_questions_soft_deleted_excluded(
        self,
        client: AsyncClient,
        sample_city: CityModel,
        sample_city_question: CityQuestionModel,
        test_session: AsyncSession,
    ):
        """Soft delete된 질문은 조회되지 않음."""
        # Given: 질문을 soft delete
        sample_city_question.deleted_at = datetime.now(get_settings().timezone)
        await test_session.commit()

        # When
        response = await client.get(
            f"/api/v1/city-questions?city_id={sample_city.city_id.hex}",
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert len(data["list"]) == 0

    async def test_get_city_questions_empty_list_for_city_without_questions(
        self,
        client: AsyncClient,
        test_session: AsyncSession,
    ):
        """질문이 없는 도시 조회 시 빈 리스트 반환."""
        # Given: 질문이 없는 새 도시 생성
        now = datetime.now(get_settings().timezone)
        city = CityModel(
            city_id=Id().value,
            name="로렌시아",
            theme="회복의 도시",
            description="회복에 대해 생각하는 도시",
            image_url="https://example.com/lorencia.jpg",
            base_cost_points=100,
            base_duration_hours=1,
            is_active=True,
            display_order=2,
            created_at=now,
            updated_at=now,
        )
        test_session.add(city)
        await test_session.commit()

        # When
        response = await client.get(
            f"/api/v1/city-questions?city_id={city.city_id.hex}",
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["list"] == []

    async def test_get_city_questions_empty_list_for_nonexistent_city(
        self,
        client: AsyncClient,
    ):
        """존재하지 않는 도시 ID로 조회 시 빈 리스트 반환."""
        # Given
        nonexistent_city_id = Id().value.hex

        # When
        response = await client.get(
            f"/api/v1/city-questions?city_id={nonexistent_city_id}",
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["list"] == []

    async def test_get_city_questions_requires_city_id(
        self,
        client: AsyncClient,
    ):
        """city_id 파라미터 필수."""
        # When
        response = await client.get("/api/v1/city-questions")

        # Then
        assert response.status_code == 422  # Validation Error

    async def test_get_city_questions_invalid_city_id_format(
        self,
        client: AsyncClient,
    ):
        """잘못된 형식의 city_id로 조회 시 에러."""
        # When
        response = await client.get(
            "/api/v1/city-questions?city_id=invalid-uuid",
        )

        # Then
        # 잘못된 형식이면 400 Bad Request
        assert response.status_code == 400


class TestCityQuestionFlow:
    """도시 질문 플로우 통합 테스트."""

    async def test_city_questions_different_cities(
        self,
        client: AsyncClient,
        test_session: AsyncSession,
    ):
        """각 도시는 별도의 질문 목록을 가짐."""
        now = datetime.now(get_settings().timezone)

        # Given: 두 도시 생성
        city1 = CityModel(
            city_id=Id().value,
            name="세렌시아",
            theme="관계의 도시",
            description="관계에 대해 생각하는 도시",
            image_url="https://example.com/serencia.jpg",
            base_cost_points=100,
            base_duration_hours=1,
            is_active=True,
            display_order=1,
            created_at=now,
            updated_at=now,
        )
        city2 = CityModel(
            city_id=Id().value,
            name="로렌시아",
            theme="회복의 도시",
            description="회복에 대해 생각하는 도시",
            image_url="https://example.com/lorencia.jpg",
            base_cost_points=100,
            base_duration_hours=1,
            is_active=True,
            display_order=2,
            created_at=now,
            updated_at=now,
        )
        test_session.add(city1)
        test_session.add(city2)
        await test_session.flush()

        # 각 도시에 다른 질문 생성
        question1 = CityQuestionModel(
            city_question_id=Id().value,
            city_id=city1.city_id,
            question="세렌시아 질문입니다.",
            display_order=1,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        question2 = CityQuestionModel(
            city_question_id=Id().value,
            city_id=city2.city_id,
            question="로렌시아 질문입니다.",
            display_order=1,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        test_session.add(question1)
        test_session.add(question2)
        await test_session.commit()

        # When: 각 도시의 질문 조회
        response1 = await client.get(f"/api/v1/city-questions?city_id={city1.city_id.hex}")
        response2 = await client.get(f"/api/v1/city-questions?city_id={city2.city_id.hex}")

        # Then: 각 도시는 해당 도시의 질문만 반환
        assert response1.status_code == 200
        assert response2.status_code == 200

        list1 = response1.json()["list"]
        list2 = response2.json()["list"]

        assert len(list1) == 1
        assert len(list2) == 1
        assert list1[0]["question"] == "세렌시아 질문입니다."
        assert list2[0]["question"] == "로렌시아 질문입니다."
