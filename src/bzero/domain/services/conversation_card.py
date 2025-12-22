"""대화 카드 도메인 서비스 (비동기).

대화 카드의 조회, 랜덤 선택 등 핵심 비즈니스 로직을 처리합니다.
"""

import random

from bzero.domain.entities import ConversationCard
from bzero.domain.errors import NotFoundConversationCardError
from bzero.domain.repositories.conversation_card import ConversationCardRepository
from bzero.domain.value_objects import Id


class ConversationCardService:
    """대화 카드 도메인 서비스 (비동기).

    대화 카드 조회 및 랜덤 선택 기능을 제공합니다.

    Attributes:
        _conversation_card_repository: 대화 카드 저장소 (비동기)
    """

    def __init__(self, conversation_card_repository: ConversationCardRepository):
        """ConversationCardService를 초기화합니다.

        Args:
            conversation_card_repository: 대화 카드 저장소 인터페이스
        """
        self._conversation_card_repository = conversation_card_repository

    async def get_random_card(self, city_id: Id) -> ConversationCard:
        """도시별 활성화된 대화 카드 중 랜덤으로 1개를 선택합니다.

        도시 전용 카드와 공통 카드를 모두 포함하여 선택합니다.
        1. 도시 전용 카드 조회
        2. 공통 카드 조회
        3. 두 리스트를 합쳐서 랜덤 선택

        Args:
            city_id: 도시 ID

        Returns:
            랜덤으로 선택된 대화 카드

        Raises:
            NotFoundConversationCardError: 활성화된 카드가 없는 경우
        """
        # 1. 도시 전용 카드 조회
        city_cards = await self._conversation_card_repository.find_active_cards_by_city(city_id)

        # 2. 공통 카드 조회
        common_cards = await self._conversation_card_repository.find_active_common_cards()

        # 3. 두 리스트 합치기
        all_cards = city_cards + common_cards

        if not all_cards:
            raise NotFoundConversationCardError

        # 4. 랜덤 선택
        return random.choice(all_cards)

    async def get_active_cards_by_city(self, city_id: Id) -> list[ConversationCard]:
        """도시별 활성화된 대화 카드 목록을 조회합니다.

        도시 전용 카드와 공통 카드를 모두 포함합니다.

        Args:
            city_id: 도시 ID

        Returns:
            활성화된 대화 카드 목록
        """
        city_cards = await self._conversation_card_repository.find_active_cards_by_city(city_id)
        common_cards = await self._conversation_card_repository.find_active_common_cards()
        return city_cards + common_cards

    async def get_card_by_id(self, card_id: Id) -> ConversationCard:
        """대화 카드를 ID로 조회합니다.

        Args:
            card_id: 조회할 카드 ID

        Returns:
            조회된 대화 카드

        Raises:
            NotFoundConversationCardError: 카드를 찾을 수 없는 경우
        """
        card = await self._conversation_card_repository.find_by_id(card_id)
        if card is None:
            raise NotFoundConversationCardError
        return card
