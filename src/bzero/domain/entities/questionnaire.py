from dataclasses import dataclass
from datetime import datetime

from bzero.domain.value_objects import Id, QuestionAnswer


@dataclass
class Questionnaire:
    """문답지 엔티티

    도시별 질문에 대한 사용자의 답변을 나타냅니다.
    도시별로 하나의 문답지만 작성 가능합니다.
    """

    questionnaire_id: Id
    user_id: Id
    city_id: Id  # 관련 도시
    question_1_answer: QuestionAnswer
    question_2_answer: QuestionAnswer
    question_3_answer: QuestionAnswer
    has_earned_points: bool  # 포인트 지급 여부 (도시별 1회)

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @classmethod
    def create(
        cls,
        user_id: Id,
        city_id: Id,
        question_1_answer: QuestionAnswer,
        question_2_answer: QuestionAnswer,
        question_3_answer: QuestionAnswer,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Questionnaire":
        """새 Questionnaire 엔티티를 생성합니다 (ID 자동 생성)."""
        return cls(
            questionnaire_id=Id(),
            user_id=user_id,
            city_id=city_id,
            question_1_answer=question_1_answer,
            question_2_answer=question_2_answer,
            question_3_answer=question_3_answer,
            has_earned_points=False,
            created_at=created_at,
            updated_at=updated_at,
        )

    def mark_points_earned(self) -> None:
        """포인트 지급 완료 표시"""
        self.has_earned_points = True
