import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bzero.core.settings import get_settings
from bzero.domain.entities import Airship
from bzero.infrastructure.repositories.airship import SqlAlchemyAirshipRepository


def get_seed(timezone: ZoneInfo) -> list[Airship]:
    now = datetime.now(timezone)
    return [
        Airship.create(
            name="일반 비행선",
            description="기본 비행선입니다. 느긋하게 여행을 즐기며 도시로 이동합니다.",
            image_url="https://spphmqtqpxauvvgntilq.supabase.co/storage/v1/object/public/images/img_express_airship.webp",
            cost_factor=1,
            duration_factor=3,
            display_order=1,
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        Airship.create(
            name="고속 비행선",
            description="빠른 비행선입니다. 신속하게 도시로 이동합니다.",
            image_url="https://spphmqtqpxauvvgntilq.supabase.co/storage/v1/object/public/images/img_normal_airship.webp",
            cost_factor=3,
            duration_factor=1,
            display_order=2,
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
    ]


async def seed_airships():
    settings = get_settings()
    engine = create_async_engine(settings.database.async_url, echo=True)

    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        airship_repository = SqlAlchemyAirshipRepository(session)
        for airship in get_seed(settings.timezone):
            await airship_repository.create(airship)
        await session.commit()


if __name__ == "__main__":
    print("=" * 60)
    print("B0 비행선 Seed Data 생성")
    print("=" * 60)
    print()

    asyncio.run(seed_airships())

    print()
    print("=" * 60)
    print("완료!")
    print("=" * 60)
