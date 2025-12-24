"""대화 카드 시드 데이터 생성 스크립트.

도시별 대화 카드와 공통 대화 카드를 생성합니다.
"""

import asyncio
from datetime import datetime

from sqlalchemy import select

from bzero.core.database import get_async_db_session, setup_db_connection
from bzero.core.settings import get_settings
from bzero.domain.entities import ConversationCard
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.conversation_card_model import ConversationCardModel
from bzero.infrastructure.repositories.conversation_card import SqlAlchemyConversationCardRepository


# 공통 대화 카드 (모든 도시에서 사용 가능)
COMMON_CARDS = [
    {"question": "오늘 하루 중 가장 행복했던 순간은 무엇인가요?", "category": "일상"},
    {"question": "최근에 감사했던 일이 있나요?", "category": "일상"},
    {"question": "지금 이 순간 가장 하고 싶은 것은 무엇인가요?", "category": "일상"},
    {"question": "당신에게 가장 소중한 사람은 누구인가요?", "category": "관계"},
    {"question": "가장 기억에 남는 여행지는 어디인가요?", "category": "추억"},
    {"question": "어릴 적 꿈꿨던 직업은 무엇이었나요?", "category": "추억"},
    {"question": "당신을 가장 잘 표현하는 단어는 무엇인가요?", "category": "자아"},
    {"question": "스트레스를 받을 때 주로 어떻게 푸시나요?", "category": "일상"},
    {"question": "가장 좋아하는 계절과 그 이유는 무엇인가요?", "category": "일상"},
    {"question": "인생에서 가장 중요하게 생각하는 가치는 무엇인가요?", "category": "자아"},
]

# 도시별 대화 카드 (도시 이름을 키로 사용)
CITY_SPECIFIC_CARDS = {
    "세렌시아": [
        {"question": "당신에게 '관계'란 무엇인가요?", "category": "관계"},
        {"question": "가장 오래 간직하고 싶은 인연은 누구인가요?", "category": "관계"},
        {"question": "혼자만의 시간과 함께하는 시간 중 어떤 것이 더 소중한가요?", "category": "관계"},
    ],
    "아트리움": [
        {"question": "당신의 창작 활동이나 취미는 무엇인가요?", "category": "창의"},
        {"question": "가장 아름답다고 느꼈던 순간은 언제인가요?", "category": "창의"},
        {"question": "예술 작품 중 가장 인상 깊었던 것은 무엇인가요?", "category": "창의"},
    ],
    "템포랄리스": [
        {"question": "과거로 돌아갈 수 있다면 언제로 가고 싶나요?", "category": "시간"},
        {"question": "미래의 자신에게 하고 싶은 말이 있나요?", "category": "시간"},
        {"question": "당신에게 '지금 이 순간'은 어떤 의미인가요?", "category": "시간"},
    ],
}


async def seed_conversation_cards():
    """대화 카드 시드 데이터를 생성합니다."""
    settings = get_settings()
    setup_db_connection(settings)

    async for session in get_async_db_session():
        repository = SqlAlchemyConversationCardRepository(session)
        now = datetime.now(settings.timezone)

        try:
            # 1. 기존 카드 삭제 (재실행 시)
            print("기존 카드 삭제 중...")
            existing_cards = await session.execute(select(ConversationCardModel))
            for card in existing_cards.scalars().all():
                await session.delete(card)
            await session.flush()

            # 2. 공통 카드 생성
            print(f"\n공통 카드 {len(COMMON_CARDS)}개 생성 중...")
            for card_data in COMMON_CARDS:
                card = ConversationCard.create(
                    question=card_data["question"],
                    category=card_data["category"],
                    created_at=now,
                    updated_at=now,
                    city_id=None,  # 공통 카드
                    is_active=True,
                )
                await repository.create(card)
                print(f"  ✓ {card_data['question'][:30]}...")

            # 3. 도시별 카드 생성
            # 도시 조회
            cities = await session.execute(select(CityModel).where(CityModel.is_active == True))  # noqa: E712
            cities_map = {city.name: city for city in cities.scalars().all()}

            for city_name, cards_data in CITY_SPECIFIC_CARDS.items():
                if city_name not in cities_map:
                    print(f"\n⚠️  도시 '{city_name}' 를 찾을 수 없습니다. 건너뜁니다.")
                    continue

                city = cities_map[city_name]
                print(f"\n{city_name} 전용 카드 {len(cards_data)}개 생성 중...")
                for card_data in cards_data:
                    card = ConversationCard.create(
                        question=card_data["question"],
                        category=card_data["category"],
                        created_at=now,
                        updated_at=now,
                        city_id=Id(str(city.city_id)),
                        is_active=True,
                    )
                    await repository.create(card)
                    print(f"  ✓ {card_data['question'][:30]}...")

            # 4. 커밋
            await session.commit()
            print("\n✅ 대화 카드 시드 데이터 생성 완료!")
            print(f"   - 공통 카드: {len(COMMON_CARDS)}개")
            print(f"   - 도시별 카드: {sum(len(cards) for cards in CITY_SPECIFIC_CARDS.values())}개")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ 에러 발생: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_conversation_cards())
