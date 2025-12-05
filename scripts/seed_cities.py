"""도시 시드 데이터 생성 스크립트

6개 도시 데이터를 데이터베이스에 생성합니다.
- Phase 1: 세렌시아, 로렌시아 (활성화)
- Phase 2: 나머지 4개 도시 (비활성화)

사용법:
    uv run python scripts/seed_cities.py
"""

import asyncio
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bzero.core.settings import Settings
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.base import Base
from bzero.infrastructure.db.city_model import CityModel


# 6개 도시 데이터 정의
CITIES_DATA = [
    # Phase 1 (활성화)
    {
        "name": "세렌시아",
        "theme": "관계의 도시",
        "description": "관계에 대해 생각하고 다른 여행자들과 대화를 나누는 도시입니다.",
        "image_url": "https://example.com/cities/serencia.jpg",
        "is_active": True,
        "display_order": 1,
    },
    {
        "name": "로렌시아",
        "theme": "회복의 도시",
        "description": "지친 마음을 회복하고 휴식을 취하는 도시입니다.",
        "image_url": "https://example.com/cities/lorencia.jpg",
        "is_active": True,
        "display_order": 2,
    },
    # Phase 2 (비활성화)
    {
        "name": "에테리아",
        "theme": "성장의 도시",
        "description": "자신의 성장과 발전에 대해 성찰하는 도시입니다.",
        "image_url": "https://example.com/cities/etheria.jpg",
        "is_active": False,
        "display_order": 3,
    },
    {
        "name": "드리모스",
        "theme": "꿈의 도시",
        "description": "꿈과 상상력에 대해 탐구하는 도시입니다.",
        "image_url": "https://example.com/cities/drimos.jpg",
        "is_active": False,
        "display_order": 4,
    },
    {
        "name": "셀레니아",
        "theme": "평온의 도시",
        "description": "고요함과 평온을 경험하는 도시입니다.",
        "image_url": "https://example.com/cities/selenia.jpg",
        "is_active": False,
        "display_order": 5,
    },
    {
        "name": "아벤투라",
        "theme": "모험의 도시",
        "description": "새로운 도전과 모험을 떠나는 도시입니다.",
        "image_url": "https://example.com/cities/aventura.jpg",
        "is_active": False,
        "display_order": 6,
    },
]


async def seed_cities() -> None:
    """도시 시드 데이터를 생성합니다."""
    settings = Settings()
    engine = create_async_engine(settings.database.async_url, echo=True)

    # 테이블 생성 (필요한 경우)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 세션 생성
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        # 기존 도시 확인
        result = await session.execute(select(CityModel))
        existing_cities = result.scalars().all()

        if existing_cities:
            print(f"\n⚠️  이미 {len(existing_cities)}개의 도시가 존재합니다.")
            print("기존 도시 목록:")
            for city in existing_cities:
                status = "🟢 활성" if city.is_active else "🔴 비활성"
                print(f"  {status} {city.name} ({city.theme}) - Order: {city.display_order}")

            response = input("\n기존 데이터를 삭제하고 새로 생성하시겠습니까? (y/N): ")
            if response.lower() != "y":
                print("시드 데이터 생성을 취소했습니다.")
                return

            # 기존 데이터 삭제
            for city in existing_cities:
                await session.delete(city)
            await session.commit()
            print("✅ 기존 도시 데이터를 삭제했습니다.\n")

        # 새 도시 데이터 생성
        now = datetime.now(settings.timezone)
        cities = []

        for city_data in CITIES_DATA:
            city = CityModel(
                city_id=Id().value,
                name=city_data["name"],
                theme=city_data["theme"],
                description=city_data["description"],
                image_url=city_data["image_url"],
                is_active=city_data["is_active"],
                display_order=city_data["display_order"],
                created_at=now,
                updated_at=now,
            )
            cities.append(city)

        session.add_all(cities)
        await session.commit()

        print("✅ 도시 시드 데이터를 생성했습니다!\n")
        print("생성된 도시 목록:")
        for city in cities:
            status = "🟢 활성" if city.is_active else "🔴 비활성"
            print(f"  {status} {city.name} ({city.theme}) - Order: {city.display_order}")
            print(f"     ID: {city.city_id.hex}")

        # 활성 도시 개수 확인
        active_count = sum(1 for city in cities if city.is_active)
        print("\n📊 통계:")
        print(f"  - 총 도시: {len(cities)}개")
        print(f"  - 활성 도시 (Phase 1): {active_count}개")
        print(f"  - 비활성 도시 (Phase 2): {len(cities) - active_count}개")

    await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("B0 도시 시드 데이터 생성")
    print("=" * 60)
    print()

    asyncio.run(seed_cities())

    print()
    print("=" * 60)
    print("완료!")
    print("=" * 60)
