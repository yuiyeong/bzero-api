"""Questionnaire 엔티티 단위 테스트"""

from datetime import datetime

from bzero.domain.entities.questionnaire import Questionnaire
from bzero.domain.value_objects import Id, QuestionAnswer


class TestQuestionnaire:
    """Questionnaire 엔티티 테스트"""

    def test_create_questionnaire(self):
        """문답지를 생성할 수 있다"""
        # Given
        user_id = Id()
        city_id = Id()
        question_1_answer = QuestionAnswer("답변1")
        question_2_answer = QuestionAnswer("답변2")
        question_3_answer = QuestionAnswer("답변3")
        now = datetime.now()

        # When
        questionnaire = Questionnaire.create(
            user_id=user_id,
            city_id=city_id,
            question_1_answer=question_1_answer,
            question_2_answer=question_2_answer,
            question_3_answer=question_3_answer,
            created_at=now,
            updated_at=now,
        )

        # Then
        assert questionnaire.questionnaire_id is not None
        assert questionnaire.user_id == user_id
        assert questionnaire.city_id == city_id
        assert questionnaire.question_1_answer == question_1_answer
        assert questionnaire.question_2_answer == question_2_answer
        assert questionnaire.question_3_answer == question_3_answer
        assert questionnaire.has_earned_points is False
        assert questionnaire.deleted_at is None

    def test_mark_points_earned(self):
        """포인트 지급 완료 표시를 할 수 있다"""
        # Given
        questionnaire = Questionnaire.create(
            user_id=Id(),
            city_id=Id(),
            question_1_answer=QuestionAnswer("답변1"),
            question_2_answer=QuestionAnswer("답변2"),
            question_3_answer=QuestionAnswer("답변3"),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert questionnaire.has_earned_points is False

        # When
        questionnaire.mark_points_earned()

        # Then
        assert questionnaire.has_earned_points is True
