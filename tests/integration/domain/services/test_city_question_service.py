"""CityQuestionService 통합 테스트."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.domain.errors import NotFoundCityQuestionError
from bzero.domain.services.city_question import CityQuestionService
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.city_question_model import CityQuestionModel
from bzero.infrastructure.repositories.city_question import SqlAlchemyCityQuestionRepository


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def city_question_service(test_session: AsyncSession) -> CityQuestionService:
    """CityQuestionService fixture를 생성합니다."""
    repository = SqlAlchemyCityQuestionRepository(test_session)
    return CityQuestionService(city_question_repository=repository)


@pytest.fixture
async def sample_city(test_session: AsyncSession) -> CityModel:
    """테스트용 샘플 도시 데이터를 생성합니다."""
    now = datetime.now()
    city = CityModel(
        city_id=uuid7(),
        name="세렌시아",
        theme="관계",
        description="노을빛 항구 마을",
        image_url="https://example.com/serentia.jpg",
        base_cost_points=300,
        base_duration_hours=24,
        is_active=True,
        display_order=1,
        created_at=now,
        updated_at=now,
    )
    test_session.add(city)
    await test_session.flush()
    return city


@pytest.fixture
async def sample_city_question(
    test_session: AsyncSession,
    sample_city: CityModel,
) -> CityQuestionModel:
    """테스트용 샘플 도시 질문 데이터를 생성합니다."""
    now = datetime.now()
    question = CityQuestionModel(
        city_question_id=uuid7(),
        city_id=sample_city.city_id,
        question="오늘 가장 감사했던 순간은 언제인가요?",
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(question)
    await test_session.flush()
    return question


@pytest.fixture
async def sample_city_questions(
    test_session: AsyncSession,
    sample_city: CityModel,
) -> list[CityQuestionModel]:
    """테스트용 샘플 도시 질문 목록을 생성합니다."""
    now = datetime.now()
    questions = []
    question_texts = [
        "오늘 가장 감사했던 순간은 언제인가요?",
        "최근에 누군가에게 받은 따뜻한 말이 있나요?",
        "오늘 하루 중 가장 기억에 남는 순간은?",
    ]

    for i, text in enumerate(question_texts):
        question = CityQuestionModel(
            city_question_id=uuid7(),
            city_id=sample_city.city_id,
            question=text,
            display_order=i + 1,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        test_session.add(question)
        questions.append(question)

    await test_session.flush()
    return questions


# =============================================================================
# Tests
# =============================================================================


class TestCityQuestionServiceGetQuestionById:
    """get_question_by_id 메서드 통합 테스트."""

    async def test_get_question_by_id_success(
        self,
        city_question_service: CityQuestionService,
        sample_city_question: CityQuestionModel,
    ):
        """ID로 질문을 조회할 수 있다."""
        # When
        question = await city_question_service.get_question_by_id(Id(str(sample_city_question.city_question_id)))

        # Then
        assert question is not None
        assert str(question.city_question_id.value) == str(sample_city_question.city_question_id)
        assert question.question == sample_city_question.question

    async def test_get_question_by_id_raises_error_when_not_found(
        self,
        city_question_service: CityQuestionService,
    ):
        """존재하지 않는 질문 조회 시 NotFoundCityQuestionError 발생."""
        # Given
        non_existent_id = Id()

        # When/Then
        with pytest.raises(NotFoundCityQuestionError):
            await city_question_service.get_question_by_id(non_existent_id)


class TestCityQuestionServiceGetActiveQuestionsByCityId:
    """get_active_questions_by_city_id 메서드 통합 테스트."""

    async def test_get_active_questions_by_city_id_success(
        self,
        city_question_service: CityQuestionService,
        sample_city: CityModel,
        sample_city_questions: list[CityQuestionModel],
    ):
        """도시의 활성화된 질문 목록을 조회할 수 있다."""
        # When
        questions = await city_question_service.get_active_questions_by_city_id(Id(str(sample_city.city_id)))

        # Then
        assert len(questions) == 3

    async def test_get_active_questions_by_city_id_ordered_by_display_order(
        self,
        city_question_service: CityQuestionService,
        sample_city: CityModel,
        sample_city_questions: list[CityQuestionModel],
    ):
        """질문 목록은 display_order 오름차순으로 정렬된다."""
        # When
        questions = await city_question_service.get_active_questions_by_city_id(Id(str(sample_city.city_id)))

        # Then
        for i in range(len(questions) - 1):
            assert questions[i].display_order < questions[i + 1].display_order

    async def test_get_active_questions_by_city_id_returns_empty_list_when_no_questions(
        self,
        city_question_service: CityQuestionService,
    ):
        """질문이 없으면 빈 리스트를 반환한다."""
        # Given
        non_existent_city_id = Id()

        # When
        questions = await city_question_service.get_active_questions_by_city_id(non_existent_city_id)

        # Then
        assert questions == []
