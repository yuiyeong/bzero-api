"""대화 카드 리포지토리 인터페이스 (비동기).

도메인 계층에서 정의하는 대화 카드 저장소의 추상 인터페이스입니다.
FastAPI와 같은 비동기 환경에서 사용됩니다.
실제 구현은 Infrastructure 계층의 SqlAlchemyConversationCardRepository에서 제공합니다.
"""

from abc import ABC, abstractmethod

from bzero.domain.entities.conversation_card import ConversationCard
from bzero.domain.value_objects import Id


class ConversationCardRepository(ABC):
    """대화 카드 리포지토리 인터페이스 (비동기).

    대화 카드 엔티티의 영속성을 담당하는 추상 클래스입니다.
    모든 메서드는 async로 정의되어 비동기 I/O를 지원합니다.
    """

    @abstractmethod
    async def create(self, card: ConversationCard) -> ConversationCard:
        """대화 카드를 생성합니다.

        Args:
            card: 생성할 대화 카드 엔티티

        Returns:
            생성된 대화 카드 (DB에서 반환된 값 포함)
        """

    @abstractmethod
    async def find_by_id(self, card_id: Id) -> ConversationCard | None:
        """ID로 대화 카드를 조회합니다.

        Args:
            card_id: 조회할 카드 ID

        Returns:
            조회된 카드 또는 None
        """

    @abstractmethod
    async def find_active_cards_by_city(self, city_id: Id) -> list[ConversationCard]:
        """도시별 활성 대화 카드를 조회합니다.

        Args:
            city_id: 도시 ID

        Returns:
            활성 카드 목록 (is_active=True, deleted_at IS NULL)
        """

    @abstractmethod
    async def find_active_common_cards(self) -> list[ConversationCard]:
        """공용 활성 대화 카드를 조회합니다.

        Returns:
            공용 활성 카드 목록 (city_id IS NULL, is_active=True, deleted_at IS NULL)
        """
