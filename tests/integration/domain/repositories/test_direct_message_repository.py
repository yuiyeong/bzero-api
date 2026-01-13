"""DirectMessageRepository Integration Tests."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.domain.entities.direct_message import DirectMessage
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.direct_message_room_model import DirectMessageRoomModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.room_model import RoomModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.direct_message import (
    SqlAlchemyDirectMessageRepository,
)


@pytest.fixture
def dm_repository(test_session: AsyncSession) -> SqlAlchemyDirectMessageRepository:
    """DirectMessageRepository fixture."""
    return SqlAlchemyDirectMessageRepository(test_session)


@pytest.fixture
async def sample_users(test_session: AsyncSession) -> tuple[UserModel, UserModel]:
    """테스트용 샘플 유저 2명 생성."""
    now = datetime.now()
    user1 = UserModel(
        user_id=Id(uuid7()).value,
        email="user1@example.com",
        nickname="유저1",
        profile_emoji="👤",
        current_points=1000,
        created_at=now,
    )
    user2 = UserModel(
        user_id=Id(uuid7()).value,
        email="user2@example.com",
        nickname="유저2",
        profile_emoji="👥",
        current_points=1000,
        created_at=now,
    )
    test_session.add_all([user1, user2])
    await test_session.flush()
    return user1, user2


@pytest.fixture
async def sample_dm_room(
    test_session: AsyncSession,
    sample_users: tuple[UserModel, UserModel],
) -> DirectMessageRoomModel:
    """테스트용 대화방 생성."""
    user1, user2 = sample_users
    now = datetime.now()

    # Create a city
    city = CityModel(
        city_id=uuid7(),
        name="테스트 도시",
        theme="테스트",
        description="테스트용 도시",
        base_cost_points=100,
        base_duration_minutes=24,
        is_active=True,
        display_order=1,
        created_at=now,
    )
    test_session.add(city)

    # Create a guest house
    guest_house = GuestHouseModel(
        guest_house_id=uuid7(),
        city_id=city.city_id,
        name="테스트 게스트하우스",
        guest_house_type="WANDERER",
        created_at=now,
    )
    test_session.add(guest_house)

    # Create a room
    room = RoomModel(
        room_id=uuid7(),
        guest_house_id=guest_house.guest_house_id,
        max_capacity=10,
        current_capacity=0,
        created_at=now,
    )
    test_session.add(room)

    # Flush parent tables first
    await test_session.flush()

    # Create a DM room
    dm_room = DirectMessageRoomModel(
        dm_room_id=Id(uuid7()).value,
        guesthouse_id=guest_house.guest_house_id,
        room_id=room.room_id,
        requester_id=user1.user_id,
        receiver_id=user2.user_id,
        status="accepted",  # 메시지 테스트를 위해 ACCEPTED 상태
        started_at=now,
        created_at=now,
    )
    test_session.add(dm_room)
    await test_session.flush()
    return dm_room


@pytest.mark.asyncio
class TestDirectMessageRepository:
    """DirectMessageRepository 통합 테스트."""

    async def test_create_message(
        self,
        dm_repository: SqlAlchemyDirectMessageRepository,
        sample_dm_room: DirectMessageRoomModel,
        sample_users: tuple[UserModel, UserModel],
    ):
        """메시지 생성 테스트."""
        # Given
        user1, user2 = sample_users
        now = datetime.now()
        message = DirectMessage.create(
            dm_room_id=Id(str(sample_dm_room.dm_room_id)),
            from_user_id=Id(str(user1.user_id)),
            to_user_id=Id(str(user2.user_id)),
            content=MessageContent("안녕하세요!"),
            created_at=now,
        )

        # When
        created = await dm_repository.create(message)

        # Then
        assert created.dm_id is not None
        assert created.content.value == "안녕하세요!"
        assert created.is_read is False

    async def test_find_by_id_success(
        self,
        dm_repository: SqlAlchemyDirectMessageRepository,
        sample_dm_room: DirectMessageRoomModel,
        sample_users: tuple[UserModel, UserModel],
    ):
        """ID로 메시지 조회 성공 테스트."""
        # Given
        user1, user2 = sample_users
        now = datetime.now()
        message = DirectMessage.create(
            dm_room_id=Id(str(sample_dm_room.dm_room_id)),
            from_user_id=Id(str(user1.user_id)),
            to_user_id=Id(str(user2.user_id)),
            content=MessageContent("테스트 메시지"),
            created_at=now,
        )
        created = await dm_repository.create(message)

        # When
        found = await dm_repository.find_by_id(created.dm_id)

        # Then
        assert found is not None
        assert found.dm_id.value == created.dm_id.value

    async def test_find_by_dm_room_paginated(
        self,
        dm_repository: SqlAlchemyDirectMessageRepository,
        sample_dm_room: DirectMessageRoomModel,
        sample_users: tuple[UserModel, UserModel],
    ):
        """대화방별 메시지 페이지네이션 조회 테스트."""
        # Given: 5개 메시지 생성
        user1, user2 = sample_users
        now = datetime.now()
        for i in range(5):
            message = DirectMessage.create(
                dm_room_id=Id(str(sample_dm_room.dm_room_id)),
                from_user_id=Id(str(user1.user_id)),
                to_user_id=Id(str(user2.user_id)),
                content=MessageContent(f"메시지 {i}"),
                created_at=now + timedelta(seconds=i),
            )
            await dm_repository.create(message)

        # When: 처음 3개 조회 (오래된 순)
        messages = await dm_repository.find_by_dm_room_paginated(
            dm_room_id=Id(str(sample_dm_room.dm_room_id)),
            cursor=None,
            limit=3,
        )

        # Then: 오래된 순으로 3개 반환
        assert len(messages) == 3
        assert messages[0].content.value == "메시지 0"
        assert messages[2].content.value == "메시지 2"

        # When: cursor로 다음 2개 조회
        cursor = messages[2].dm_id
        next_messages = await dm_repository.find_by_dm_room_paginated(
            dm_room_id=Id(str(sample_dm_room.dm_room_id)),
            cursor=cursor,
            limit=3,
        )

        # Then: 다음 2개 반환
        assert len(next_messages) == 2
        assert next_messages[0].content.value == "메시지 3"
        assert next_messages[1].content.value == "메시지 4"

    async def test_mark_as_read(
        self,
        dm_repository: SqlAlchemyDirectMessageRepository,
        sample_dm_room: DirectMessageRoomModel,
        sample_users: tuple[UserModel, UserModel],
    ):
        """읽음 처리 테스트."""
        # Given: user1 -> user2 메시지 3개 생성
        user1, user2 = sample_users
        now = datetime.now()
        for i in range(3):
            message = DirectMessage.create(
                dm_room_id=Id(str(sample_dm_room.dm_room_id)),
                from_user_id=Id(str(user1.user_id)),
                to_user_id=Id(str(user2.user_id)),
                content=MessageContent(f"메시지 {i}"),
                created_at=now,
            )
            await dm_repository.create(message)

        # When: user2가 읽음 처리
        read_count = await dm_repository.mark_as_read_by_dm_room_and_user(
            dm_room_id=Id(str(sample_dm_room.dm_room_id)),
            user_id=Id(str(user2.user_id)),
        )

        # Then
        assert read_count == 3

    async def test_count_unread(
        self,
        dm_repository: SqlAlchemyDirectMessageRepository,
        sample_dm_room: DirectMessageRoomModel,
        sample_users: tuple[UserModel, UserModel],
    ):
        """읽지 않은 메시지 개수 조회 테스트."""
        # Given: user1 -> user2 메시지 2개 생성
        user1, user2 = sample_users
        now = datetime.now()
        for i in range(2):
            message = DirectMessage.create(
                dm_room_id=Id(str(sample_dm_room.dm_room_id)),
                from_user_id=Id(str(user1.user_id)),
                to_user_id=Id(str(user2.user_id)),
                content=MessageContent(f"메시지 {i}"),
                created_at=now,
            )
            await dm_repository.create(message)

        # When
        unread_count = await dm_repository.count_unread_by_dm_room_and_user(
            dm_room_id=Id(str(sample_dm_room.dm_room_id)),
            user_id=Id(str(user2.user_id)),
        )

        # Then
        assert unread_count == 2

    async def test_find_latest_by_dm_room(
        self,
        dm_repository: SqlAlchemyDirectMessageRepository,
        sample_dm_room: DirectMessageRoomModel,
        sample_users: tuple[UserModel, UserModel],
    ):
        """최신 메시지 조회 테스트."""
        # Given: 3개 메시지 생성
        user1, user2 = sample_users
        now = datetime.now()
        for i in range(3):
            message = DirectMessage.create(
                dm_room_id=Id(str(sample_dm_room.dm_room_id)),
                from_user_id=Id(str(user1.user_id)),
                to_user_id=Id(str(user2.user_id)),
                content=MessageContent(f"메시지 {i}"),
                created_at=now + timedelta(seconds=i),
            )
            await dm_repository.create(message)

        # When
        latest = await dm_repository.find_latest_by_dm_room(dm_room_id=Id(str(sample_dm_room.dm_room_id)))

        # Then
        assert latest is not None
        assert latest.content.value == "메시지 2"
