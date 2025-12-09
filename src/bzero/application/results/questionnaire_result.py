from dataclasses import dataclass
from datetime import datetime

from bzero.domain.entities.questionnaire import Questionnaire


@dataclass(frozen=True)
class QuestionnaireResult:
    """UseCase에서 반환하는 Questionnaire 결과 객체"""

    questionnaire_id: str
    user_id: str
    city_id: str
    question_1_answer: str
    question_2_answer: str
    question_3_answer: str
    has_earned_points: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_from(cls, entity: Questionnaire) -> "QuestionnaireResult":
        return cls(
            questionnaire_id=entity.questionnaire_id.value,
            user_id=entity.user_id.value,
            city_id=entity.city_id.value,
            question_1_answer=entity.question_1_answer.value,
            question_2_answer=entity.question_2_answer.value,
            question_3_answer=entity.question_3_answer.value,
            has_earned_points=entity.has_earned_points,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
