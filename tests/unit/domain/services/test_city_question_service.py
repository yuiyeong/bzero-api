"""CityQuestionService 단위 테스트."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest
from uuid_utils import uuid7

from bzero.domain.entities.city_question import CityQuestion
from bzero.domain.errors import NotFoundCityQuestionError
from bzero.domain.repositories.city_question import CityQuestionRepository
from bzero.domain.services.city_question import CityQuestionService
from bzero.domain.value_objects import Id


@pytest.fixture
def mock_city_question_repository() -> MagicMock:
    """Mock CityQuestionRepository."""
    return MagicMock(spec=CityQuestionRepository)


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone."""
    return ZoneInfo("Asia/Seoul")


@pytest.fixture
def city_question_service(mock_city_question_repository: MagicMock) -> CityQuestionService:
    """CityQuestionService with mocked repository."""
    return CityQuestionService(mock_city_question_repository)


@pytest.fixture
def sample_city_question(timezone: ZoneInfo) -> CityQuestion:
    """샘플 도시 질문."""
    now = datetime.now(timezone)
    return CityQuestion.create(
        city_id=Id(uuid7()),
        question="오늘 가장 감사했던 순간은 언제인가요?",
        display_order=1,
        created_at=now,
        updated_at=now,
    )


class TestCityQuestionServiceGetQuestionById:
    """get_question_by_id 메서드 테스트."""

    async def test_get_question_by_id_success(
        self,
        city_question_service: CityQuestionService,
        mock_city_question_repository: MagicMock,
        sample_city_question: CityQuestion,
    ):
        """질문 ID로 질문을 조회할 수 있다."""
        # Given
        mock_city_question_repository.find_by_id = AsyncMock(return_value=sample_city_question)

        # When
        question = await city_question_service.get_question_by_id(sample_city_question.city_question_id)

        # Then
        assert question.city_question_id == sample_city_question.city_question_id
        mock_city_question_repository.find_by_id.assert_called_once_with(sample_city_question.city_question_id)

    async def test_get_question_by_id_raises_error_when_not_found(
        self,
        city_question_service: CityQuestionService,
        mock_city_question_repository: MagicMock,
    ):
        """질문을 찾을 수 없으면 에러가 발생한다."""
        # Given
        question_id = Id(uuid7())
        mock_city_question_repository.find_by_id = AsyncMock(return_value=None)

        # When/Then
        with pytest.raises(NotFoundCityQuestionError):
            await city_question_service.get_question_by_id(question_id)


class TestCityQuestionServiceGetActiveQuestionsByCityId:
    """get_active_questions_by_city_id 메서드 테스트."""

    async def test_get_active_questions_by_city_id_success(
        self,
        city_question_service: CityQuestionService,
        mock_city_question_repository: MagicMock,
        sample_city_question: CityQuestion,
    ):
        """도시의 활성화된 질문 목록을 조회할 수 있다."""
        # Given
        city_id = sample_city_question.city_id
        mock_city_question_repository.find_active_by_city_id = AsyncMock(return_value=[sample_city_question])

        # When
        questions = await city_question_service.get_active_questions_by_city_id(city_id)

        # Then
        assert len(questions) == 1
        assert questions[0].city_id == city_id
        mock_city_question_repository.find_active_by_city_id.assert_called_once_with(city_id)

    async def test_get_active_questions_by_city_id_returns_empty_list(
        self,
        city_question_service: CityQuestionService,
        mock_city_question_repository: MagicMock,
    ):
        """활성화된 질문이 없으면 빈 리스트를 반환한다."""
        # Given
        city_id = Id(uuid7())
        mock_city_question_repository.find_active_by_city_id = AsyncMock(return_value=[])

        # When
        questions = await city_question_service.get_active_questions_by_city_id(city_id)

        # Then
        assert questions == []

    async def test_get_active_questions_by_city_id_returns_ordered_list(
        self,
        city_question_service: CityQuestionService,
        mock_city_question_repository: MagicMock,
        timezone: ZoneInfo,
    ):
        """질문 목록은 display_order 순으로 정렬된다."""
        # Given
        city_id = Id(uuid7())
        now = datetime.now(timezone)
        questions = [
            CityQuestion.create(
                city_id=city_id,
                question=f"질문 {i}",
                display_order=i,
                created_at=now,
                updated_at=now,
            )
            for i in range(1, 4)
        ]
        mock_city_question_repository.find_active_by_city_id = AsyncMock(return_value=questions)

        # When
        result = await city_question_service.get_active_questions_by_city_id(city_id)

        # Then
        assert len(result) == 3
        assert result[0].display_order == 1
        assert result[1].display_order == 2
        assert result[2].display_order == 3
