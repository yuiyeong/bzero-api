from dataclasses import dataclass
from datetime import datetime

from bzero.domain.entities.questionnaire import Questionnaire


@dataclass(frozen=True)
class QuestionnaireResult:
    """문답지 조회 결과.

    Attributes:
        questionnaire_id: 문답지 ID
        user_id: 작성자 ID
        room_stay_id: 체류 ID
        city_question_id: 질문 ID
        city_question: 도시 질문 내용 (스냅샷)
        answer: 답변 내용
        city_id: 도시 ID
        guest_house_id: 게스트하우스 ID
        created_at: 생성 시간
        updated_at: 수정 시간
    """

    questionnaire_id: str
    user_id: str
    room_stay_id: str
    city_question_id: str
    city_question: str
    answer: str
    city_id: str
    guest_house_id: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_from(cls, entity: Questionnaire) -> "QuestionnaireResult":
        """Questionnaire 엔티티에서 QuestionnaireResult를 생성합니다.

        Args:
            entity: Questionnaire 엔티티

        Returns:
            QuestionnaireResult 인스턴스
        """
        return cls(
            questionnaire_id=entity.questionnaire_id.to_hex(),
            user_id=entity.user_id.to_hex(),
            room_stay_id=entity.room_stay_id.to_hex(),
            city_question_id=entity.city_question_id.to_hex(),
            city_question=entity.city_question,
            answer=entity.answer,
            city_id=entity.city_id.to_hex(),
            guest_house_id=entity.guest_house_id.to_hex(),
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
