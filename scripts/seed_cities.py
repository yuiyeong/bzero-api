"""도시 시드 데이터 생성 스크립트

6개 도시 데이터를 데이터베이스에 생성합니다.
- Phase 1: 세렌시아, 로렌시아 (활성화)
- Phase 2: 나머지 4개 도시 (비활성화)

사용법:
    uv run python scripts/seed_cities.py
"""

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bzero.core.settings import get_settings
from bzero.domain.entities import City
from bzero.infrastructure.repositories.city import SqlAlchemyCityRepository


def get_seed(timezone: ZoneInfo) -> list[City]:
    now = datetime.now(timezone)
    return [
        # Phase 1 (활성화)
        City.create(
            name="세렌시아",
            theme="관계의 도시",
            description="관계에 대해 생각하고 다른 여행자들과 대화를 나누는 도시입니다.",
            image_url="https://spphmqtqpxauvvgntilq.supabase.co/storage/v1/object/public/images/icon_serensia.webp",
            base_cost_points=100,
            base_duration_hours=3,
            is_active=True,
            display_order=1,
            created_at=now,
            updated_at=now,
        ),
        City.create(
            name="로렌시아",
            theme="회복의 도시",
            description="지친 마음을 회복하고 휴식을 취하는 도시입니다.",
            image_url="https://spphmqtqpxauvvgntilq.supabase.co/storage/v1/object/public/images/icon_lorensia.webp",
            base_cost_points=100,
            base_duration_hours=3,
            is_active=True,
            display_order=2,
            created_at=now,
            updated_at=now,
        ),
        # Phase 2 (비활성화)
        City.create(
            name="엠마시아",
            theme="희망의 도시",
            description="꿈과 상상력에 대해 탐구하는 도시입니다.",
            image_url="https://spphmqtqpxauvvgntilq.supabase.co/storage/v1/object/public/images/icon_emmasia.webp",
            base_cost_points=100,
            base_duration_hours=3,
            is_active=False,
            display_order=3,
            created_at=now,
            updated_at=now,
        ),
        City.create(
            name="다마린",
            theme="고요의 도시",
            description="고요함과 평온을 경험하는 도시입니다.",
            image_url="https://spphmqtqpxauvvgntilq.supabase.co/storage/v1/object/public/images/icon_damarin.webp",
            base_cost_points=100,
            base_duration_hours=3,
            is_active=False,
            display_order=4,
            created_at=now,
            updated_at=now,
        ),
        City.create(
            name="갈리시아",
            theme="성찰의 도시",
            description="자신의 성장과 발전에 대해 성찰하는 도시입니다.",
            image_url="https://spphmqtqpxauvvgntilq.supabase.co/storage/v1/object/public/images/icon_damarin.webp",
            base_cost_points=100,
            base_duration_hours=3,
            is_active=False,
            display_order=5,
            created_at=now,
            updated_at=now,
        ),
    ]


async def seed_cities():
    settings = get_settings()
    engine = create_async_engine(settings.database.async_url, echo=True)

    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        city_repository = SqlAlchemyCityRepository(session)
        for city in get_seed(settings.timezone):
            await city_repository.create(city)
        await session.commit()


if __name__ == "__main__":
    print("=" * 60)
    print("B0 도시 Seed Data 생성")
    print("=" * 60)
    print()

    asyncio.run(seed_cities())

    print()
    print("=" * 60)
    print("완료!")
    print("=" * 60)
