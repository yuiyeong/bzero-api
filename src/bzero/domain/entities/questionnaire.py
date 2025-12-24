from dataclasses import dataclass
from datetime import datetime

from bzero.domain.errors import InvalidQuestionnaireAnswerError
from bzero.domain.value_objects import Id


@dataclass
class Questionnaire:
    """문답지 엔티티.

    체류 중 도시 질문에 대한 답변입니다. 1문 1답 형식으로,
    체류당 같은 질문에 1개의 답변만 작성 가능합니다.
    작성 시 50P를 획득합니다.

    Attributes:
        questionnaire_id: 문답지 고유 식별자 (UUID v7)
        user_id: 작성자 ID (FK)
        room_stay_id: 체류 ID (FK)
        city_question_id: 질문 ID (FK)
        city_question: 도시 질문 내용 (스냅샷)
        answer: 답변 내용
        city_id: 도시 ID (FK, 비정규화)
        guest_house_id: 게스트하우스 ID (FK, 비정규화)
        created_at: 생성 시각
        updated_at: 수정 시각
        deleted_at: 삭제 시각 (soft delete)

    도메인 규칙:
        - 체류당 같은 질문에 1개의 답변만 가능
        - 최초 작성 시에만 포인트 지급 (50P)
        - 수정/삭제는 언제든지 가능
    """

    questionnaire_id: Id
    user_id: Id
    room_stay_id: Id
    city_question_id: Id
    city_question: str
    answer: str
    city_id: Id
    guest_house_id: Id
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        """유효성 검사를 수행합니다."""
        if not self.answer:
            raise InvalidQuestionnaireAnswerError

    def update_answer(
        self,
        answer_text: str,
        updated_at: datetime,
    ) -> None:
        """답변 내용을 수정합니다.

        Args:
            answer_text: 새 답변 내용
            updated_at: 수정 시각

        Raises:
            InvalidQuestionnaireAnswerError: 답변 내용이 유효하지 않은 경우
        """
        self._validate_answer(answer_text)
        self.answer = answer_text
        self.updated_at = updated_at

    def soft_delete(self, deleted_at: datetime) -> None:
        """문답지를 soft delete 처리합니다.

        Args:
            deleted_at: 삭제 시각
        """
        self.deleted_at = deleted_at
        self.updated_at = deleted_at

    @staticmethod
    def _validate_answer(answer: str) -> None:
        """답변 내용의 유효성을 검사합니다.

        Args:
            answer: 검사할 답변 내용

        Raises:
            InvalidQuestionnaireAnswerError: 답변 내용이 유효하지 않은 경우
        """
        if not answer:
            raise InvalidQuestionnaireAnswerError

    @classmethod
    def create(
        cls,
        user_id: Id,
        room_stay_id: Id,
        city_question_id: Id,
        city_question: str,
        answer: str,
        city_id: Id,
        guest_house_id: Id,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Questionnaire":
        """새 문답지 엔티티를 생성합니다.

        Args:
            user_id: 작성자 ID
            room_stay_id: 체류 ID
            city_question_id: 질문 ID
            city_question: 도시 질문 내용 (스냅샷)
            answer: 답변 내용
            city_id: 도시 ID
            guest_house_id: 게스트하우스 ID
            created_at: 생성 시각
            updated_at: 수정 시각

        Returns:
            새로 생성된 Questionnaire 엔티티 (ID 자동 생성)

        Raises:
            InvalidQuestionnaireAnswerError: 답변 내용이 유효하지 않은 경우
        """
        return cls(
            questionnaire_id=Id(),
            user_id=user_id,
            room_stay_id=room_stay_id,
            city_question_id=city_question_id,
            city_question=city_question,
            answer=answer,
            city_id=city_id,
            guest_house_id=guest_house_id,
            created_at=created_at,
            updated_at=updated_at,
        )
