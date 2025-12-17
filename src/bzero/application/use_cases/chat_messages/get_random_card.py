"""랜덤 대화 카드 조회 유스케이스.

도시별 활성화된 대화 카드 중 랜덤으로 1개를 선택하는 비즈니스 로직을 담당합니다.
"""

from bzero.application.results import ConversationCardResult
from bzero.domain.services import ConversationCardService
from bzero.domain.value_objects import Id


class GetRandomCardUseCase:
    """랜덤 대화 카드 조회 유스케이스.

    도시 전용 카드와 공통 카드를 모두 포함하여 랜덤으로 선택합니다.
    """

    def __init__(self, conversation_card_service: ConversationCardService):
        """GetRandomCardUseCase를 초기화합니다.

        Args:
            conversation_card_service: 대화 카드 도메인 서비스
        """
        self._conversation_card_service = conversation_card_service

    async def execute(self, city_id: str) -> ConversationCardResult:
        """랜덤 대화 카드 조회를 실행합니다.

        Args:
            city_id: 도시 ID (hex 문자열)

        Returns:
            랜덤으로 선택된 대화 카드 정보

        Raises:
            NotFoundConversationCardError: 활성화된 카드가 없는 경우
        """
        # 1. 랜덤 카드 선택 (도시 전용 + 공통 카드)
        card = await self._conversation_card_service.get_random_card(Id.from_hex(city_id))

        return ConversationCardResult.create_from(card)
