"""대화 카드 엔티티.

룸 내 여행자들이 대화를 시작할 수 있는 주제를 제공하는 카드를 나타냅니다.
도시별 테마 카드와 공용 카드로 구분됩니다.
"""

from dataclasses import dataclass
from datetime import datetime

from bzero.domain.value_objects import Id


@dataclass
class ConversationCard:
    """대화 카드 엔티티.

    Attributes:
        card_id: 카드 고유 식별자 (UUID v7)
        city_id: 도시 ID (None이면 공용 카드)
        question: 대화 질문 내용
        category: 카드 카테고리 (예: 관계, 회복, 일상, 상상)
        is_active: 활성화 여부
        created_at: 생성 일시
        updated_at: 수정 일시
        deleted_at: 삭제 일시 (soft delete)
    """

    card_id: Id
    city_id: Id | None
    question: str
    category: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    def activate(self) -> None:
        """카드를 활성화합니다."""
        self.is_active = True

    def deactivate(self) -> None:
        """카드를 비활성화합니다."""
        self.is_active = False

    @property
    def is_common_card(self) -> bool:
        """공용 카드 여부를 반환합니다."""
        return self.city_id is None

    @classmethod
    def create(
        cls,
        question: str,
        category: str | None,
        created_at: datetime,
        updated_at: datetime,
        city_id: Id | None = None,
        is_active: bool = True,
    ) -> "ConversationCard":
        """대화 카드를 생성합니다.

        Args:
            question: 대화 질문 내용
            category: 카드 카테고리 (선택사항)
            created_at: 생성 일시
            updated_at: 수정 일시
            city_id: 도시 ID (None이면 공용 카드)
            is_active: 활성화 여부 (기본값: True)

        Returns:
            새로 생성된 ConversationCard 엔티티
        """
        return cls(
            card_id=Id(),
            city_id=city_id,
            question=question,
            category=category,
            is_active=is_active,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=None,
        )
