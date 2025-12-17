from dataclasses import dataclass
from datetime import datetime

from bzero.domain.entities import ConversationCard


@dataclass
class ConversationCardResult:
    """대화 카드 결과 객체.

    Use Case와 API 응답 사이의 데이터 변환을 담당합니다.
    """

    card_id: str
    city_id: str | None
    question: str
    category: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_from(cls, entity: ConversationCard) -> "ConversationCardResult":
        """ConversationCard 엔티티로부터 결과 객체를 생성합니다.

        Args:
            entity: ConversationCard 엔티티

        Returns:
            ConversationCardResult 인스턴스
        """
        return cls(
            card_id=entity.card_id.to_hex(),
            city_id=entity.city_id.to_hex() if entity.city_id else None,
            question=entity.question,
            category=entity.category,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
