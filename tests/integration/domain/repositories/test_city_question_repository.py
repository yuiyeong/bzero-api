"""CityQuestionRepository 통합 테스트."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.domain.entities.city_question import CityQuestion
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.city_question_model import CityQuestionModel
from bzero.infrastructure.repositories.city_question import SqlAlchemyCityQuestionRepository


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def city_question_repository(test_session: AsyncSession) -> SqlAlchemyCityQuestionRepository:
    """CityQuestionRepository fixture를 생성합니다."""
    return SqlAlchemyCityQuestionRepository(test_session)


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
        "지금 이 순간 가장 편안하게 느껴지는 것은 무엇인가요?",
        "비활성화된 질문입니다.",
    ]

    for i, text in enumerate(question_texts):
        question = CityQuestionModel(
            city_question_id=uuid7(),
            city_id=sample_city.city_id,
            question=text,
            display_order=i + 1,
            is_active=(i < 4),  # 마지막 질문은 비활성화
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


class TestCityQuestionRepositoryCreate:
    """CityQuestionRepository.create() 메서드 테스트."""

    async def test_create_city_question_success(
        self,
        city_question_repository: SqlAlchemyCityQuestionRepository,
        sample_city: CityModel,
    ):
        """새로운 도시 질문을 생성할 수 있어야 합니다."""
        # Given
        now = datetime.now()
        question = CityQuestion.create(
            city_id=Id(str(sample_city.city_id)),
            question="새로운 질문입니다.",
            display_order=1,
            created_at=now,
            updated_at=now,
        )

        # When
        created = await city_question_repository.create(question)

        # Then
        assert created is not None
        assert str(created.city_question_id.value) == str(question.city_question_id.value)
        assert str(created.city_id.value) == str(sample_city.city_id)
        assert created.question == "새로운 질문입니다."
        assert created.display_order == 1
        assert created.is_active is True


class TestCityQuestionRepositoryFindById:
    """CityQuestionRepository.find_by_id() 메서드 테스트."""

    async def test_find_by_id_success(
        self,
        city_question_repository: SqlAlchemyCityQuestionRepository,
        sample_city_question: CityQuestionModel,
    ):
        """ID로 질문을 조회할 수 있어야 합니다."""
        # When
        question = await city_question_repository.find_by_id(Id(str(sample_city_question.city_question_id)))

        # Then
        assert question is not None
        assert str(question.city_question_id.value) == str(sample_city_question.city_question_id)
        assert question.question == sample_city_question.question

    async def test_find_by_id_returns_none_when_not_found(
        self,
        city_question_repository: SqlAlchemyCityQuestionRepository,
    ):
        """존재하지 않는 ID로 조회 시 None을 반환해야 합니다."""
        # Given
        non_existent_id = Id()

        # When
        question = await city_question_repository.find_by_id(non_existent_id)

        # Then
        assert question is None

    async def test_find_by_id_soft_deleted_excluded(
        self,
        city_question_repository: SqlAlchemyCityQuestionRepository,
        sample_city_question: CityQuestionModel,
        test_session: AsyncSession,
    ):
        """Soft delete된 질문은 조회되지 않아야 합니다."""
        # Given: 질문을 soft delete
        sample_city_question.deleted_at = datetime.now()
        await test_session.flush()

        # When
        question = await city_question_repository.find_by_id(Id(str(sample_city_question.city_question_id)))

        # Then
        assert question is None


class TestCityQuestionRepositoryFindActiveByCityId:
    """CityQuestionRepository.find_active_by_city_id() 메서드 테스트."""

    async def test_find_active_by_city_id_success(
        self,
        city_question_repository: SqlAlchemyCityQuestionRepository,
        sample_city: CityModel,
        sample_city_questions: list[CityQuestionModel],
    ):
        """도시 ID로 활성화된 질문 목록을 조회할 수 있어야 합니다."""
        # When
        questions = await city_question_repository.find_active_by_city_id(Id(str(sample_city.city_id)))

        # Then
        assert len(questions) == 4  # 5개 중 4개만 활성화
        assert all(q.is_active for q in questions)

    async def test_find_active_by_city_id_ordered_by_display_order(
        self,
        city_question_repository: SqlAlchemyCityQuestionRepository,
        sample_city: CityModel,
        sample_city_questions: list[CityQuestionModel],
    ):
        """질문 목록은 display_order 오름차순으로 정렬되어야 합니다."""
        # When
        questions = await city_question_repository.find_active_by_city_id(Id(str(sample_city.city_id)))

        # Then
        for i in range(len(questions) - 1):
            assert questions[i].display_order < questions[i + 1].display_order

    async def test_find_active_by_city_id_returns_empty_list(
        self,
        city_question_repository: SqlAlchemyCityQuestionRepository,
    ):
        """해당 도시에 활성화된 질문이 없으면 빈 리스트를 반환해야 합니다."""
        # Given
        non_existent_city_id = Id()

        # When
        questions = await city_question_repository.find_active_by_city_id(non_existent_city_id)

        # Then
        assert questions == []

    async def test_find_active_by_city_id_soft_deleted_excluded(
        self,
        city_question_repository: SqlAlchemyCityQuestionRepository,
        sample_city: CityModel,
        sample_city_questions: list[CityQuestionModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 질문은 조회되지 않아야 합니다."""
        # Given: 첫 번째 질문을 soft delete
        sample_city_questions[0].deleted_at = datetime.now()
        await test_session.flush()

        # When
        questions = await city_question_repository.find_active_by_city_id(Id(str(sample_city.city_id)))

        # Then
        assert len(questions) == 3  # 4개 중 1개 삭제
        assert all(str(q.city_question_id.value) != str(sample_city_questions[0].city_question_id) for q in questions)


class TestCityQuestionRepositoryUpdate:
    """CityQuestionRepository.update() 메서드 테스트."""

    async def test_update_city_question_success(
        self,
        city_question_repository: SqlAlchemyCityQuestionRepository,
        sample_city_question: CityQuestionModel,
    ):
        """질문을 업데이트할 수 있어야 합니다."""
        # Given
        question = await city_question_repository.find_by_id(Id(str(sample_city_question.city_question_id)))
        assert question is not None

        question.deactivate()

        # When
        updated = await city_question_repository.update(question)

        # Then
        assert updated is not None
        assert updated.is_active is False
