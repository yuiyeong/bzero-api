"""DirectMessageRoomRepository Integration Tests."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.domain.entities.direct_message_room import DirectMessageRoom
from bzero.domain.value_objects import DMStatus, Id
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.room_model import RoomModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.direct_message_room import (
    SqlAlchemyDirectMessageRoomRepository,
)


@pytest.fixture
def dm_room_repository(test_session: AsyncSession) -> SqlAlchemyDirectMessageRoomRepository:
    """DirectMessageRoomRepository fixture."""
    return SqlAlchemyDirectMessageRoomRepository(test_session)


@pytest.fixture
async def sample_users(test_session: AsyncSession) -> tuple[UserModel, UserModel]:
    """테스트용 샘플 유저 2명 생성."""
    now = datetime.now()
    user1 = UserModel(
        user_id=uuid7(),
        email="user1@example.com",
        nickname="유저1",
        profile_emoji="👤",
        current_points=1000,
        created_at=now,
        updated_at=now,
    )
    user2 = UserModel(
        user_id=uuid7(),
        email="user2@example.com",
        nickname="유저2",
        profile_emoji="👥",
        current_points=1000,
        created_at=now,
        updated_at=now,
    )
    test_session.add_all([user1, user2])
    await test_session.flush()
    return user1, user2


@pytest.fixture
async def sample_room(test_session: AsyncSession) -> RoomModel:
    """테스트용 샘플 룸 데이터."""
    now = datetime.now()

    # Create a city
    city = CityModel(
        city_id=uuid7(),
        name="테스트 도시",
        theme="테스트",
        description="테스트용 도시",
        base_cost_points=100,
        base_duration_hours=24,
        is_active=True,
        display_order=1,
        created_at=now,
        updated_at=now,
    )
    test_session.add(city)

    # Create a guest house
    guest_house = GuestHouseModel(
        guest_house_id=uuid7(),
        city_id=city.city_id,
        name="테스트 게스트하우스",
        guest_house_type="WANDERER",
        created_at=now,
        updated_at=now,
    )
    test_session.add(guest_house)

    # Create a room
    room = RoomModel(
        room_id=uuid7(),
        guest_house_id=guest_house.guest_house_id,
        max_capacity=10,
        current_capacity=0,
        created_at=now,
        updated_at=now,
    )
    test_session.add(room)
    await test_session.flush()
    return room


@pytest.mark.asyncio
class TestDirectMessageRoomRepository:
    """DirectMessageRoomRepository 통합 테스트."""

    async def test_create_dm_room(
        self,
        dm_room_repository: SqlAlchemyDirectMessageRoomRepository,
        sample_users: tuple[UserModel, UserModel],
        sample_room: RoomModel,
    ):
        """대화방 생성 테스트."""
        # Given
        user1, user2 = sample_users
        now = datetime.now()
        dm_room = DirectMessageRoom.create(
            guesthouse_id=Id(str(sample_room.guest_house_id)),
            room_id=Id(str(sample_room.room_id)),
            user1_id=Id(str(user1.user_id)),
            user2_id=Id(str(user2.user_id)),
            created_at=now,
            updated_at=now,
        )

        # When
        created = await dm_room_repository.create(dm_room)

        # Then
        assert created.dm_room_id is not None
        assert created.status == DMStatus.PENDING
        # Value is UUID, need to compare as strings
        assert str(created.user1_id.value) == str(user1.user_id)
        assert str(created.user2_id.value) == str(user2.user_id)

    async def test_find_by_id_success(
        self,
        dm_room_repository: SqlAlchemyDirectMessageRoomRepository,
        sample_users: tuple[UserModel, UserModel],
        sample_room: RoomModel,
    ):
        """ID로 대화방 조회 성공 테스트."""
        # Given
        user1, user2 = sample_users
        now = datetime.now()
        dm_room = DirectMessageRoom.create(
            guesthouse_id=Id(str(sample_room.guest_house_id)),
            room_id=Id(str(sample_room.room_id)),
            user1_id=Id(str(user1.user_id)),
            user2_id=Id(str(user2.user_id)),
            created_at=now,
            updated_at=now,
        )
        created = await dm_room_repository.create(dm_room)

        # When
        found = await dm_room_repository.find_by_id(created.dm_room_id)

        # Then
        assert found is not None
        assert found.dm_room_id.value == created.dm_room_id.value
        assert found.status == DMStatus.PENDING

    async def test_find_by_id_not_found(
        self,
        dm_room_repository: SqlAlchemyDirectMessageRoomRepository,
    ):
        """존재하지 않는 ID 조회 테스트."""
        # When
        found = await dm_room_repository.find_by_id(Id())

        # Then
        assert found is None

    async def test_find_by_room_and_users(
        self,
        dm_room_repository: SqlAlchemyDirectMessageRoomRepository,
        sample_users: tuple[UserModel, UserModel],
        sample_room: RoomModel,
    ):
        """룸과 사용자로 대화방 조회 테스트."""
        # Given
        user1, user2 = sample_users
        now = datetime.now()
        dm_room = DirectMessageRoom.create(
            guesthouse_id=Id(str(sample_room.guest_house_id)),
            room_id=Id(str(sample_room.room_id)),
            user1_id=Id(str(user1.user_id)),
            user2_id=Id(str(user2.user_id)),
            created_at=now,
            updated_at=now,
        )
        await dm_room_repository.create(dm_room)

        # When: 정방향 조회
        found = await dm_room_repository.find_by_room_and_users(
            room_id=Id(str(sample_room.room_id)),
            user1_id=Id(str(user1.user_id)),
            user2_id=Id(str(user2.user_id)),
        )

        # Then
        assert found is not None

        # When: 역방향 조회 (user1 <-> user2)
        found_reverse = await dm_room_repository.find_by_room_and_users(
            room_id=Id(str(sample_room.room_id)),
            user1_id=Id(str(user2.user_id)),
            user2_id=Id(str(user1.user_id)),
        )

        # Then
        assert found_reverse is not None
        assert found_reverse.dm_room_id.value == found.dm_room_id.value

    async def test_find_by_user_and_statuses(
        self,
        dm_room_repository: SqlAlchemyDirectMessageRoomRepository,
        sample_users: tuple[UserModel, UserModel],
        sample_room: RoomModel,
        test_session: AsyncSession,
    ):
        """사용자와 상태로 대화방 목록 조회 테스트."""
        # Given
        user1, user2 = sample_users
        now = datetime.now()

        # Create additional users for different DM rooms
        user3 = UserModel(
            user_id=uuid7(),
            email="user3@example.com",
            nickname="유저3",
            profile_emoji="👩",
            current_points=1000,
            created_at=now,
            updated_at=now,
        )
        test_session.add(user3)
        await test_session.flush()

        # Create DM room with user1 and user2
        dm_room1 = DirectMessageRoom.create(
            guesthouse_id=Id(str(sample_room.guest_house_id)),
            room_id=Id(str(sample_room.room_id)),
            user1_id=Id(str(user1.user_id)),
            user2_id=Id(str(user2.user_id)),
            created_at=now,
            updated_at=now,
        )
        await dm_room_repository.create(dm_room1)

        # Create DM room with user1 and user3 (different pair)
        dm_room2 = DirectMessageRoom.create(
            guesthouse_id=Id(str(sample_room.guest_house_id)),
            room_id=Id(str(sample_room.room_id)),
            user1_id=Id(str(user1.user_id)),
            user2_id=Id(str(user3.user_id)),
            created_at=now,
            updated_at=now,
        )
        await dm_room_repository.create(dm_room2)

        # When
        rooms = await dm_room_repository.find_by_user_and_statuses(
            user_id=Id(str(user1.user_id)),
            statuses=[DMStatus.PENDING],
        )

        # Then
        assert len(rooms) >= 2

    async def test_update_dm_room(
        self,
        dm_room_repository: SqlAlchemyDirectMessageRoomRepository,
        sample_users: tuple[UserModel, UserModel],
        sample_room: RoomModel,
    ):
        """대화방 업데이트 테스트."""
        # Given
        user1, user2 = sample_users
        now = datetime.now()
        dm_room = DirectMessageRoom.create(
            guesthouse_id=Id(str(sample_room.guest_house_id)),
            room_id=Id(str(sample_room.room_id)),
            user1_id=Id(str(user1.user_id)),
            user2_id=Id(str(user2.user_id)),
            created_at=now,
            updated_at=now,
        )
        created = await dm_room_repository.create(dm_room)

        # When: 상태 변경
        created.accept(now)
        updated = await dm_room_repository.update(created)

        # Then
        assert updated.status == DMStatus.ACCEPTED
        assert updated.started_at is not None

    async def test_count_by_user_and_statuses(
        self,
        dm_room_repository: SqlAlchemyDirectMessageRoomRepository,
        sample_users: tuple[UserModel, UserModel],
        sample_room: RoomModel,
    ):
        """사용자와 상태별 대화방 개수 조회 테스트."""
        # Given
        user1, user2 = sample_users
        now = datetime.now()
        dm_room = DirectMessageRoom.create(
            guesthouse_id=Id(str(sample_room.guest_house_id)),
            room_id=Id(str(sample_room.room_id)),
            user1_id=Id(str(user1.user_id)),
            user2_id=Id(str(user2.user_id)),
            created_at=now,
            updated_at=now,
        )
        await dm_room_repository.create(dm_room)

        # When
        count = await dm_room_repository.count_by_user_and_statuses(
            user_id=Id(str(user1.user_id)),
            statuses=[DMStatus.PENDING],
        )

        # Then
        assert count >= 1
