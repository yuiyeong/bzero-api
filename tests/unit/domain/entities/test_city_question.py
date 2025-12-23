"""CityQuestion 엔티티 단위 테스트."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.entities.city_question import CityQuestion
from bzero.domain.errors import InvalidCityQuestionError
from bzero.domain.value_objects import Id


class TestCityQuestion:
    """CityQuestion 엔티티 단위 테스트."""

    @pytest.fixture
    def tz(self) -> ZoneInfo:
        """Seoul timezone."""
        return get_settings().timezone

    def test_create_city_question(self, tz: ZoneInfo):
        """도시 질문을 생성할 수 있다."""
        # Given
        city_id = Id(uuid7())
        question_text = "오늘 가장 감사했던 순간은 언제인가요?"
        display_order = 1
        now = datetime.now(tz)

        # When
        question = CityQuestion.create(
            city_id=city_id,
            question=question_text,
            display_order=display_order,
            created_at=now,
            updated_at=now,
        )

        # Then
        assert question.city_question_id is not None
        assert question.city_id == city_id
        assert question.question == question_text
        assert question.display_order == display_order
        assert question.is_active is True
        assert question.created_at == now
        assert question.updated_at == now
        assert question.deleted_at is None

    def test_create_city_question_generates_id(self, tz: ZoneInfo):
        """도시 질문 생성 시 city_question_id가 자동 생성된다."""
        # Given
        now = datetime.now(tz)

        # When
        question = CityQuestion.create(
            city_id=Id(uuid7()),
            question="질문 내용입니다.",
            display_order=1,
            created_at=now,
            updated_at=now,
        )

        # Then
        assert question.city_question_id is not None
        assert isinstance(question.city_question_id, Id)

    def test_create_city_question_with_max_length(self, tz: ZoneInfo):
        """최대 길이(500자)의 질문을 생성할 수 있다."""
        # Given
        now = datetime.now(tz)
        question_text = "a" * 500  # MAX_QUESTION_LENGTH = 500

        # When
        question = CityQuestion.create(
            city_id=Id(uuid7()),
            question=question_text,
            display_order=1,
            created_at=now,
            updated_at=now,
        )

        # Then
        assert len(question.question) == 500

    def test_create_city_question_with_inactive(self, tz: ZoneInfo):
        """비활성화 상태로 질문을 생성할 수 있다."""
        # Given
        now = datetime.now(tz)

        # When
        question = CityQuestion.create(
            city_id=Id(uuid7()),
            question="질문 내용입니다.",
            display_order=1,
            is_active=False,
            created_at=now,
            updated_at=now,
        )

        # Then
        assert question.is_active is False

    def test_create_city_question_with_empty_text_raises_error(self, tz: ZoneInfo):
        """빈 질문 내용으로 생성하면 에러가 발생한다."""
        # Given
        now = datetime.now(tz)

        # When/Then
        with pytest.raises(InvalidCityQuestionError):
            CityQuestion.create(
                city_id=Id(uuid7()),
                question="",
                display_order=1,
                created_at=now,
                updated_at=now,
            )

    def test_create_city_question_with_invalid_display_order_raises_error(self, tz: ZoneInfo):
        """display_order가 1 미만이면 에러가 발생한다."""
        # Given
        now = datetime.now(tz)

        # When/Then
        with pytest.raises(InvalidCityQuestionError):
            CityQuestion.create(
                city_id=Id(uuid7()),
                question="질문 내용입니다.",
                display_order=0,
                created_at=now,
                updated_at=now,
            )

    def test_create_city_question_with_negative_display_order_raises_error(self, tz: ZoneInfo):
        """display_order가 음수이면 에러가 발생한다."""
        # Given
        now = datetime.now(tz)

        # When/Then
        with pytest.raises(InvalidCityQuestionError):
            CityQuestion.create(
                city_id=Id(uuid7()),
                question="질문 내용입니다.",
                display_order=-1,
                created_at=now,
                updated_at=now,
            )

    def test_activate(self, tz: ZoneInfo):
        """질문을 활성화할 수 있다."""
        # Given
        now = datetime.now(tz)
        question = CityQuestion.create(
            city_id=Id(uuid7()),
            question="질문 내용입니다.",
            display_order=1,
            is_active=False,
            created_at=now,
            updated_at=now,
        )
        assert question.is_active is False

        # When
        question.activate()

        # Then
        assert question.is_active is True

    def test_deactivate(self, tz: ZoneInfo):
        """질문을 비활성화할 수 있다."""
        # Given
        now = datetime.now(tz)
        question = CityQuestion.create(
            city_id=Id(uuid7()),
            question="질문 내용입니다.",
            display_order=1,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert question.is_active is True

        # When
        question.deactivate()

        # Then
        assert question.is_active is False

    def test_soft_delete(self, tz: ZoneInfo):
        """질문을 soft delete 처리할 수 있다."""
        # Given
        now = datetime.now(tz)
        question = CityQuestion.create(
            city_id=Id(uuid7()),
            question="질문 내용입니다.",
            display_order=1,
            created_at=now,
            updated_at=now,
        )
        delete_time = datetime.now(tz)

        # When
        question.soft_delete(deleted_at=delete_time)

        # Then
        assert question.deleted_at == delete_time
        assert question.updated_at == delete_time
