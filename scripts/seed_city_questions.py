"""도시별 질문 시드 데이터 생성 스크립트

도시별 질문 데이터를 데이터베이스에 생성합니다.
- 세렌시아 (관계의 도시): 3개 질문
- 로렌시아 (회복의 도시): 3개 질문

사용법:
    uv run python scripts/seed_city_questions.py

주의: 반드시 seed_cities.py를 먼저 실행해야 합니다.
"""

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bzero.core.settings import get_settings
from bzero.domain.entities.city_question import CityQuestion
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.repositories.city_question import SqlAlchemyCityQuestionRepository


# 도시별 질문 데이터
CITY_QUESTIONS = {
    "세렌시아": [
        "오늘 누군가에게 고마웠던 순간이 있었나요?",
        "최근 마음이 통했다고 느낀 대화가 있었나요?",
        "지금 떠오르는 소중한 사람에게 하고 싶은 말이 있다면?",
    ],
    "로렌시아": [
        "오늘 나를 위해 했던 작은 일이 있었나요?",
        "요즘 나에게 필요한 휴식은 어떤 모습일까요?",
        "지친 나에게 해주고 싶은 말이 있다면?",
    ],
}


async def get_city_id_by_name(session: AsyncSession, name: str) -> Id | None:
    """도시 이름으로 도시 ID를 조회합니다."""
    stmt = select(CityModel.city_id).where(
        CityModel.name == name,
        CityModel.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    city_id = result.scalar_one_or_none()
    return Id(str(city_id)) if city_id else None


def get_seed(city_id: Id, questions: list[str], timezone: ZoneInfo) -> list[CityQuestion]:
    """도시의 질문 시드 데이터를 생성합니다."""
    now = datetime.now(timezone)
    return [
        CityQuestion.create(
            city_id=city_id,
            question=question,
            display_order=i + 1,
            created_at=now,
            updated_at=now,
        )
        for i, question in enumerate(questions)
    ]


async def seed_city_questions():
    settings = get_settings()
    engine = create_async_engine(settings.database.async_url, echo=True)

    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        city_question_repository = SqlAlchemyCityQuestionRepository(session)

        for city_name, questions in CITY_QUESTIONS.items():
            print(f"\n{city_name} 질문 생성 중...")

            # 도시 ID 조회
            city_id = await get_city_id_by_name(session, city_name)
            if city_id is None:
                print(f"  ⚠️  '{city_name}' 도시를 찾을 수 없습니다. seed_cities.py를 먼저 실행하세요.")
                continue

            # 질문 생성
            for city_question in get_seed(city_id, questions, settings.timezone):
                await city_question_repository.create(city_question)
                print(f"  ✓ {city_question.question}")

        await session.commit()


if __name__ == "__main__":
    print("=" * 60)
    print("B0 도시별 질문 Seed Data 생성")
    print("=" * 60)

    asyncio.run(seed_city_questions())

    print()
    print("=" * 60)
    print("완료!")
    print("=" * 60)
