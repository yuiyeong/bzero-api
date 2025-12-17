"""ConversationCardRepository Integration Tests."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.domain.entities import ConversationCard
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.conversation_card_model import ConversationCardModel
from bzero.infrastructure.repositories.conversation_card import SqlAlchemyConversationCardRepository


@pytest.fixture
def conversation_card_repository(test_session: AsyncSession) -> SqlAlchemyConversationCardRepository:
    """ConversationCardRepository fixture를 생성합니다."""
    return SqlAlchemyConversationCardRepository(test_session)


@pytest.fixture
async def sample_city(test_session: AsyncSession) -> CityModel:
    """테스트용 샘플 도시 데이터를 생성합니다."""
    now = datetime.now()
    city = CityModel(
        city_id=uuid7(),
        name="세렌시아",
        theme="관계",
        description="노을빛 항구 마을",
        image_url="https://example.com/serentia.jpg",
        base_cost_points=300,
        base_duration_hours=24,
        is_active=True,
        display_order=1,
        created_at=now,
        updated_at=now,
    )
    test_session.add(city)
    await test_session.flush()
    return city


@pytest.mark.asyncio
class TestConversationCardRepository:
    """ConversationCardRepository 통합 테스트."""

    async def test_create_common_card(
        self,
        conversation_card_repository: SqlAlchemyConversationCardRepository,
    ):
        """공통 카드 생성 테스트."""
        # Given: 공통 카드 엔티티 (city_id = None)
        now = datetime.now()
        card = ConversationCard.create(
            question="당신의 행복한 순간은?",
            category="일상",
            created_at=now,
            updated_at=now,
            city_id=None,
            is_active=True,
        )

        # When: 카드 생성
        created = await conversation_card_repository.create(card)

        # Then: 생성 성공 및 필드 검증
        assert created.card_id is not None
        assert created.city_id is None
        assert created.question == "당신의 행복한 순간은?"
        assert created.category == "일상"
        assert created.is_active is True

    async def test_create_city_specific_card(
        self,
        conversation_card_repository: SqlAlchemyConversationCardRepository,
        sample_city: CityModel,
    ):
        """도시 전용 카드 생성 테스트."""
        # Given: 도시 전용 카드 엔티티
        now = datetime.now()
        card = ConversationCard.create(
            question="이 도시에서 가장 기억에 남는 장소는?",
            category="관계",
            created_at=now,
            updated_at=now,
            city_id=Id(str(sample_city.city_id)),
            is_active=True,
        )

        # When: 카드 생성
        created = await conversation_card_repository.create(card)

        # Then: 생성 성공 및 필드 검증
        assert created.city_id == Id(str(sample_city.city_id))
        assert created.question == "이 도시에서 가장 기억에 남는 장소는?"

    async def test_find_by_id_success(
        self,
        conversation_card_repository: SqlAlchemyConversationCardRepository,
        test_session: AsyncSession,
    ):
        """ID로 카드 조회 성공 테스트."""
        # Given: DB에 카드 저장
        now = datetime.now()
        card_id = uuid7()
        model = ConversationCardModel(
            card_id=card_id,
            city_id=None,
            question="테스트 질문",
            category="테스트",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        test_session.add(model)
        await test_session.flush()

        # When: ID로 조회
        found = await conversation_card_repository.find_by_id(Id(str(card_id)))

        # Then: 조회 성공
        assert found is not None
        assert found.card_id == Id(str(card_id))
        assert found.question == "테스트 질문"

    async def test_find_by_id_not_found(
        self,
        conversation_card_repository: SqlAlchemyConversationCardRepository,
    ):
        """ID로 카드 조회 실패 테스트."""
        # When: 존재하지 않는 ID로 조회
        found = await conversation_card_repository.find_by_id(Id())

        # Then: None 반환
        assert found is None

    async def test_find_active_cards_by_city(
        self,
        conversation_card_repository: SqlAlchemyConversationCardRepository,
        test_session: AsyncSession,
        sample_city: CityModel,
    ):
        """도시별 활성 카드 조회 테스트."""
        # Given: 도시 전용 카드 3개 생성
        now = datetime.now()
        for i in range(3):
            model = ConversationCardModel(
                card_id=uuid7(),
                city_id=sample_city.city_id,
                question=f"질문 {i}",
                category="관계",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            test_session.add(model)

        # Given: 비활성 카드 1개 (조회되지 않아야 함)
        inactive_model = ConversationCardModel(
            card_id=uuid7(),
            city_id=sample_city.city_id,
            question="비활성 질문",
            category="관계",
            is_active=False,
            created_at=now,
            updated_at=now,
        )
        test_session.add(inactive_model)
        await test_session.flush()

        # When: 도시별 활성 카드 조회
        cards = await conversation_card_repository.find_active_cards_by_city(Id(str(sample_city.city_id)))

        # Then: 활성 카드 3개만 반환
        assert len(cards) == 3
        assert all(card.is_active for card in cards)

    async def test_find_active_common_cards(
        self,
        conversation_card_repository: SqlAlchemyConversationCardRepository,
        test_session: AsyncSession,
    ):
        """공통 활성 카드 조회 테스트."""
        # Given: 공통 카드 5개 생성
        now = datetime.now()
        for i in range(5):
            model = ConversationCardModel(
                card_id=uuid7(),
                city_id=None,  # 공통 카드
                question=f"공통 질문 {i}",
                category="일상",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            test_session.add(model)

        # Given: 비활성 공통 카드 1개 (조회되지 않아야 함)
        inactive_model = ConversationCardModel(
            card_id=uuid7(),
            city_id=None,
            question="비활성 공통 질문",
            category="일상",
            is_active=False,
            created_at=now,
            updated_at=now,
        )
        test_session.add(inactive_model)
        await test_session.flush()

        # When: 공통 활성 카드 조회
        cards = await conversation_card_repository.find_active_common_cards()

        # Then: 활성 공통 카드 5개만 반환
        assert len(cards) == 5
        assert all(card.city_id is None for card in cards)
        assert all(card.is_active for card in cards)

    async def test_find_active_cards_empty(
        self,
        conversation_card_repository: SqlAlchemyConversationCardRepository,
        sample_city: CityModel,
    ):
        """활성 카드가 없는 경우 테스트."""
        # When: 카드가 없는 도시 조회
        cards = await conversation_card_repository.find_active_cards_by_city(Id(str(sample_city.city_id)))

        # Then: 빈 리스트 반환
        assert len(cards) == 0
