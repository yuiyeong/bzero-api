import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bzero.core.settings import get_settings
from bzero.domain.entities import GuestHouse
from bzero.infrastructure.repositories.city import SqlAlchemyCityRepository
from bzero.infrastructure.repositories.guest_house import SqlAlchemyGuestHouseRepository


async def seed_guest_houses():
    settings = get_settings()
    engine = create_async_engine(settings.database.async_url, echo=True)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        city_repository = SqlAlchemyCityRepository(session)
        guest_house_repository = SqlAlchemyGuestHouseRepository(session)

        now = datetime.now(settings.timezone)
        cities = await city_repository.find_active_cities()

        for city in cities:
            await guest_house_repository.create(
                GuestHouse.create(
                    city_id=city.city_id,
                    name="편안함이 가득한 곳",
                    description="멋진 사람들과 함께 소중한 시간을 보내세요.",
                    image_url=city.image_url,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
            )

        await session.commit()
    await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("B0 게스트하우스 Seed Data 생성")
    print("=" * 60)
    print()

    asyncio.run(seed_guest_houses())

    print()
    print("=" * 60)
    print("완료!")
    print("=" * 60)
