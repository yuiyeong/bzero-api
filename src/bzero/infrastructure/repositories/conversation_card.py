"""ConversationCard Repository 구현체 (비동기).

SqlAlchemy를 사용한 대화 카드 리포지토리 구현입니다.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities import ConversationCard
from bzero.domain.repositories.conversation_card import ConversationCardRepository
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.conversation_card_model import ConversationCardModel


class SqlAlchemyConversationCardRepository(ConversationCardRepository):
    """SqlAlchemy 기반 대화 카드 리포지토리 (비동기).

    AsyncSession을 사용하여 비동기 DB 작업을 수행합니다.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    @staticmethod
    def _to_model(entity: ConversationCard) -> ConversationCardModel:
        """ConversationCard 엔티티를 Model로 변환합니다."""
        return ConversationCardModel(
            card_id=entity.card_id.value,
            city_id=entity.city_id.value if entity.city_id else None,
            question=entity.question,
            category=entity.category,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )

    @staticmethod
    def _to_entity(model: ConversationCardModel) -> ConversationCard:
        """Model을 ConversationCard 엔티티로 변환합니다."""
        return ConversationCard(
            card_id=Id(model.card_id),
            city_id=Id(model.city_id) if model.city_id else None,
            question=model.question,
            category=model.category,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    async def create(self, card: ConversationCard) -> ConversationCard:
        """대화 카드를 생성합니다."""
        model = self._to_model(card)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def find_by_id(self, card_id: Id) -> ConversationCard | None:
        """ID로 대화 카드를 조회합니다."""
        stmt = select(ConversationCardModel).where(
            ConversationCardModel.card_id == card_id.value,
            ConversationCardModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_active_cards_by_city(self, city_id: Id) -> list[ConversationCard]:
        """도시별 활성 대화 카드를 조회합니다."""
        stmt = select(ConversationCardModel).where(
            ConversationCardModel.city_id == city_id.value,
            ConversationCardModel.is_active.is_(True),
            ConversationCardModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def find_active_common_cards(self) -> list[ConversationCard]:
        """공용 활성 대화 카드를 조회합니다."""
        stmt = select(ConversationCardModel).where(
            ConversationCardModel.city_id.is_(None),
            ConversationCardModel.is_active.is_(True),
            ConversationCardModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
