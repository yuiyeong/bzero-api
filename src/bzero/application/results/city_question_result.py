from dataclasses import dataclass
from datetime import datetime

from bzero.domain.entities.city_question import CityQuestion


@dataclass(frozen=True)
class CityQuestionResult:
    """도시 질문 조회 결과.

    Attributes:
        city_question_id: 질문 ID
        city_id: 도시 ID
        question: 질문 내용
        display_order: 표시 순서
        is_active: 활성화 여부
        created_at: 생성 시간
        updated_at: 수정 시간
    """

    city_question_id: str
    city_id: str
    question: str
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_from(cls, entity: CityQuestion) -> "CityQuestionResult":
        """CityQuestion 엔티티에서 CityQuestionResult를 생성합니다.

        Args:
            entity: CityQuestion 엔티티

        Returns:
            CityQuestionResult 인스턴스
        """
        return cls(
            city_question_id=entity.city_question_id.to_hex(),
            city_id=entity.city_id.to_hex(),
            question=entity.question,
            display_order=entity.display_order,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
