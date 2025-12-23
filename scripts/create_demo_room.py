"""채팅 데모용 룸 생성 스크립트.

데모용 고정 룸 ID를 가진 룸을 데이터베이스에 생성합니다.
"""

import asyncio
from datetime import datetime
from uuid import UUID

from bzero.core.database import get_async_db_session, setup_db_connection
from bzero.core.settings import get_settings
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.room_model import RoomModel


# 데모용 고정 ID들
DEMO_CITY_ID = UUID("00000000-0000-0000-0000-000000000001")
DEMO_GUEST_HOUSE_ID = UUID("00000000-0000-0000-0000-000000000002")
DEMO_ROOM_ID = UUID("00000000-0000-0000-0000-000000000000")


async def create_demo_room():
    """데모용 룸을 생성합니다."""
    settings = get_settings()
    setup_db_connection(settings)

    async for session in get_async_db_session():
        try:
            now = datetime.now(settings.timezone)

            # 1. 데모 도시 생성 (이미 있으면 skip)
            city = await session.get(CityModel, DEMO_CITY_ID)
            if not city:
                city = CityModel(
                    city_id=DEMO_CITY_ID,
                    name="채팅 데모 도시",
                    theme="테스트",
                    description="채팅 데모를 위한 테스트용 도시입니다.",
                    base_cost_points=0,
                    base_duration_hours=24,
                    is_active=True,
                    display_order=999,
                    created_at=now,
                    updated_at=now,
                )
                session.add(city)
                print(f"✅ 데모 도시 생성: {city.name}")
            else:
                print(f"ℹ️  데모 도시 이미 존재: {city.name}")

            # 2. 데모 게스트하우스 생성 (이미 있으면 skip)
            guest_house = await session.get(GuestHouseModel, DEMO_GUEST_HOUSE_ID)
            if not guest_house:
                guest_house = GuestHouseModel(
                    guest_house_id=DEMO_GUEST_HOUSE_ID,
                    city_id=DEMO_CITY_ID,
                    name="채팅 데모 게스트하우스",
                    guest_house_type="WANDERER",
                    created_at=now,
                    updated_at=now,
                )
                session.add(guest_house)
                print(f"✅ 데모 게스트하우스 생성: {guest_house.name}")
            else:
                print(f"ℹ️  데모 게스트하우스 이미 존재: {guest_house.name}")

            # 3. 데모 룸 생성 (이미 있으면 skip)
            room = await session.get(RoomModel, DEMO_ROOM_ID)
            if not room:
                room = RoomModel(
                    room_id=DEMO_ROOM_ID,
                    guest_house_id=DEMO_GUEST_HOUSE_ID,
                    max_capacity=100,  # 데모용이므로 큰 값
                    current_capacity=0,
                    created_at=now,
                    updated_at=now,
                )
                session.add(room)
                print(f"✅ 데모 룸 생성: {room.room_id}")
            else:
                print(f"ℹ️  데모 룸 이미 존재: {room.room_id}")

            # 4. 커밋
            await session.commit()
            print("\n🎉 채팅 데모용 룸 설정 완료!")
            print(f"   - 도시 ID: {DEMO_CITY_ID}")
            print(f"   - 게스트하우스 ID: {DEMO_GUEST_HOUSE_ID}")
            print(f"   - 룸 ID: {DEMO_ROOM_ID}")

        except Exception as e:
            await session.rollback()
            print(f"❌ 에러 발생: {e}")
            raise
        finally:
            break


if __name__ == "__main__":
    asyncio.run(create_demo_room())
