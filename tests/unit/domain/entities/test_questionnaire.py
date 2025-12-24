"""Questionnaire 엔티티 단위 테스트."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.entities.questionnaire import Questionnaire
from bzero.domain.errors import InvalidQuestionnaireAnswerError
from bzero.domain.value_objects import Id


class TestQuestionnaire:
    """Questionnaire 엔티티 단위 테스트."""

    @pytest.fixture
    def tz(self) -> ZoneInfo:
        """Seoul timezone."""
        return get_settings().timezone

    def test_create_questionnaire(self, tz: ZoneInfo):
        """문답지를 생성할 수 있다."""
        # Given
        user_id = Id(uuid7())
        room_stay_id = Id(uuid7())
        city_question_id = Id(uuid7())
        city_question = "오늘 가장 감사했던 순간은 언제인가요?"
        answer_text = "오늘 아침에 친구가 커피를 사줬어요."
        city_id = Id(uuid7())
        guest_house_id = Id(uuid7())
        now = datetime.now(tz)

        # When
        questionnaire = Questionnaire.create(
            user_id=user_id,
            room_stay_id=room_stay_id,
            city_question_id=city_question_id,
            city_question=city_question,
            answer=answer_text,
            city_id=city_id,
            guest_house_id=guest_house_id,
            created_at=now,
            updated_at=now,
        )

        # Then
        assert questionnaire.questionnaire_id is not None
        assert questionnaire.user_id == user_id
        assert questionnaire.room_stay_id == room_stay_id
        assert questionnaire.city_question_id == city_question_id
        assert questionnaire.city_question == city_question
        assert questionnaire.answer == answer_text
        assert questionnaire.city_id == city_id
        assert questionnaire.guest_house_id == guest_house_id
        assert questionnaire.created_at == now
        assert questionnaire.updated_at == now
        assert questionnaire.deleted_at is None

    def test_create_questionnaire_generates_id(self, tz: ZoneInfo):
        """문답지 생성 시 questionnaire_id가 자동 생성된다."""
        # Given
        now = datetime.now(tz)

        # When
        questionnaire = Questionnaire.create(
            user_id=Id(uuid7()),
            room_stay_id=Id(uuid7()),
            city_question_id=Id(uuid7()),
            city_question="오늘 가장 감사했던 순간은 언제인가요?",
            answer="답변 내용입니다.",
            city_id=Id(uuid7()),
            guest_house_id=Id(uuid7()),
            created_at=now,
            updated_at=now,
        )

        # Then
        assert questionnaire.questionnaire_id is not None
        assert isinstance(questionnaire.questionnaire_id, Id)

    def test_create_questionnaire_with_max_length(self, tz: ZoneInfo):
        """최대 길이(200자)의 답변을 작성할 수 있다."""
        # Given
        now = datetime.now(tz)
        answer_text = "a" * 200  # MAX_ANSWER_LENGTH = 200

        # When
        questionnaire = Questionnaire.create(
            user_id=Id(uuid7()),
            room_stay_id=Id(uuid7()),
            city_question_id=Id(uuid7()),
            city_question="오늘 가장 감사했던 순간은 언제인가요?",
            answer=answer_text,
            city_id=Id(uuid7()),
            guest_house_id=Id(uuid7()),
            created_at=now,
            updated_at=now,
        )

        # Then
        assert len(questionnaire.answer) == 200

    def test_create_questionnaire_with_empty_answer_raises_error(self, tz: ZoneInfo):
        """빈 답변으로 생성하면 에러가 발생한다."""
        # Given
        now = datetime.now(tz)

        # When/Then
        with pytest.raises(InvalidQuestionnaireAnswerError):
            Questionnaire.create(
                user_id=Id(uuid7()),
                room_stay_id=Id(uuid7()),
                city_question_id=Id(uuid7()),
                city_question="오늘 가장 감사했던 순간은 언제인가요?",
                answer="",
                city_id=Id(uuid7()),
                guest_house_id=Id(uuid7()),
                created_at=now,
                updated_at=now,
            )

    def test_update_answer(self, tz: ZoneInfo):
        """답변을 수정할 수 있다."""
        # Given
        now = datetime.now(tz)
        questionnaire = Questionnaire.create(
            user_id=Id(uuid7()),
            room_stay_id=Id(uuid7()),
            city_question_id=Id(uuid7()),
            city_question="오늘 가장 감사했던 순간은 언제인가요?",
            answer="원래 답변입니다.",
            city_id=Id(uuid7()),
            guest_house_id=Id(uuid7()),
            created_at=now,
            updated_at=now,
        )
        new_answer = "수정된 답변입니다."
        update_time = datetime.now(tz)

        # When
        questionnaire.update_answer(
            answer_text=new_answer,
            updated_at=update_time,
        )

        # Then
        assert questionnaire.answer == new_answer
        assert questionnaire.updated_at == update_time

    def test_update_answer_with_empty_text_raises_error(self, tz: ZoneInfo):
        """수정 시 빈 답변은 에러가 발생한다."""
        # Given
        now = datetime.now(tz)
        questionnaire = Questionnaire.create(
            user_id=Id(uuid7()),
            room_stay_id=Id(uuid7()),
            city_question_id=Id(uuid7()),
            city_question="오늘 가장 감사했던 순간은 언제인가요?",
            answer="원래 답변입니다.",
            city_id=Id(uuid7()),
            guest_house_id=Id(uuid7()),
            created_at=now,
            updated_at=now,
        )

        # When/Then
        with pytest.raises(InvalidQuestionnaireAnswerError):
            questionnaire.update_answer(
                answer_text="",
                updated_at=datetime.now(tz),
            )

    def test_soft_delete(self, tz: ZoneInfo):
        """문답지를 soft delete 처리할 수 있다."""
        # Given
        now = datetime.now(tz)
        questionnaire = Questionnaire.create(
            user_id=Id(uuid7()),
            room_stay_id=Id(uuid7()),
            city_question_id=Id(uuid7()),
            city_question="오늘 가장 감사했던 순간은 언제인가요?",
            answer="답변 내용입니다.",
            city_id=Id(uuid7()),
            guest_house_id=Id(uuid7()),
            created_at=now,
            updated_at=now,
        )
        delete_time = datetime.now(tz)

        # When
        questionnaire.soft_delete(deleted_at=delete_time)

        # Then
        assert questionnaire.deleted_at == delete_time
        assert questionnaire.updated_at == delete_time
