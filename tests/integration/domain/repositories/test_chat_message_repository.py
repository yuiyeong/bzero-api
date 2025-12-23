"""ChatMessageRepository Integration Tests."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.domain.entities import ChatMessage
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent, MessageType
from bzero.infrastructure.db.chat_message_model import ChatMessageModel
from bzero.infrastructure.db.conversation_card_model import ConversationCardModel
from bzero.infrastructure.db.room_model import RoomModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.chat_message import (
    SqlAlchemyChatMessageRepository,
)


@pytest.fixture
def chat_message_repository(test_session: AsyncSession) -> SqlAlchemyChatMessageRepository:
    """ChatMessageRepository fixture를 생성합니다."""
    return SqlAlchemyChatMessageRepository(test_session)


@pytest.fixture
async def sample_user(test_session: AsyncSession) -> UserModel:
    """테스트용 샘플 유저 데이터를 생성합니다."""
    now = datetime.now()
    user = UserModel(
        user_id=uuid7(),
        email="test@example.com",
        nickname="테스트유저",
        profile_emoji="👤",
        current_points=1000,
        created_at=now,
        updated_at=now,
    )
    test_session.add(user)
    await test_session.flush()
    return user


@pytest.fixture
async def sample_room(test_session: AsyncSession) -> RoomModel:
    """테스트용 샘플 룸 데이터를 생성합니다."""
    from bzero.infrastructure.db.city_model import CityModel
    from bzero.infrastructure.db.guest_house_model import GuestHouseModel

    now = datetime.now()

    # Create a city first
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


@pytest.fixture
async def sample_card(test_session: AsyncSession) -> ConversationCardModel:
    """테스트용 샘플 대화 카드를 생성합니다."""
    now = datetime.now()
    card = ConversationCardModel(
        card_id=uuid7(),
        city_id=None,  # 공통 카드
        question="당신의 행복한 순간은?",
        category="관계",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(card)
    await test_session.flush()
    return card


@pytest.mark.asyncio
class TestChatMessageRepository:
    """ChatMessageRepository 통합 테스트."""

    async def test_create_text_message(
        self,
        chat_message_repository: SqlAlchemyChatMessageRepository,
        sample_user: UserModel,
        sample_room: RoomModel,
    ):
        """텍스트 메시지 생성 테스트."""
        # Given: 텍스트 메시지 엔티티
        now = datetime.now()
        message = ChatMessage.create(
            room_id=Id(str(sample_room.room_id)),
            user_id=Id(str(sample_user.user_id)),
            content=MessageContent("안녕하세요!"),
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(days=3),
        )

        # When: 메시지 생성
        created = await chat_message_repository.create(message)

        # Then: 생성 성공 및 필드 검증
        assert created.message_id is not None
        assert created.room_id == message.room_id
        assert created.user_id == message.user_id
        assert created.content.value == "안녕하세요!"
        assert created.message_type == MessageType.TEXT
        assert created.is_system is False
        # expires_at이 3일 후로 설정되었는지 확인 (날짜만 비교)
        assert created.expires_at.date() == (now + timedelta(days=3)).date()

    async def test_create_system_message(
        self,
        chat_message_repository: SqlAlchemyChatMessageRepository,
        sample_room: RoomModel,
    ):
        """시스템 메시지 생성 테스트."""
        # Given: 시스템 메시지 엔티티
        now = datetime.now()
        message = ChatMessage.create_system_message(
            room_id=Id(str(sample_room.room_id)),
            content=MessageContent("사용자가 입장했습니다."),
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(days=3),
        )

        # When: 메시지 생성
        created = await chat_message_repository.create(message)

        # Then: 생성 성공 및 필드 검증
        assert created.user_id is None
        assert created.is_system is True
        assert created.message_type == MessageType.SYSTEM

    async def test_create_card_shared_message(
        self,
        chat_message_repository: SqlAlchemyChatMessageRepository,
        sample_user: UserModel,
        sample_room: RoomModel,
        sample_card: ConversationCardModel,
    ):
        """카드 공유 메시지 생성 테스트."""
        # Given: 카드 공유 메시지 엔티티
        now = datetime.now()
        message = ChatMessage.create_card_shared_message(
            room_id=Id(str(sample_room.room_id)),
            user_id=Id(str(sample_user.user_id)),
            card_id=Id(str(sample_card.card_id)),
            content=MessageContent(sample_card.question),
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(days=3),
        )

        # When: 메시지 생성
        created = await chat_message_repository.create(message)

        # Then: 생성 성공 및 필드 검증
        assert created.message_type == MessageType.CARD_SHARED
        assert created.card_id == Id(str(sample_card.card_id))
        assert created.content.value == sample_card.question

    async def test_find_by_id_success(
        self,
        chat_message_repository: SqlAlchemyChatMessageRepository,
        test_session: AsyncSession,
        sample_user: UserModel,
        sample_room: RoomModel,
    ):
        """ID로 메시지 조회 성공 테스트."""
        # Given: DB에 메시지 저장
        now = datetime.now()
        message_id = uuid7()
        model = ChatMessageModel(
            message_id=message_id,
            room_id=sample_room.room_id,
            user_id=sample_user.user_id,
            content="테스트 메시지",
            message_type=MessageType.TEXT.value,
            is_system=False,
            expires_at=now + timedelta(days=3),
            created_at=now,
            updated_at=now,
        )
        test_session.add(model)
        await test_session.flush()

        # When: ID로 조회
        found = await chat_message_repository.find_by_id(Id(str(message_id)))

        # Then: 조회 성공
        assert found is not None
        assert found.message_id == Id(str(message_id))
        assert found.content.value == "테스트 메시지"

    async def test_find_by_id_not_found(
        self,
        chat_message_repository: SqlAlchemyChatMessageRepository,
    ):
        """ID로 메시지 조회 실패 테스트."""
        # When: 존재하지 않는 ID로 조회
        found = await chat_message_repository.find_by_id(Id())

        # Then: None 반환
        assert found is None

    async def test_find_by_room_id_paginated(
        self,
        chat_message_repository: SqlAlchemyChatMessageRepository,
        test_session: AsyncSession,
        sample_user: UserModel,
        sample_room: RoomModel,
    ):
        """룸별 메시지 페이지네이션 조회 테스트."""
        # Given: 룸에 10개 메시지 생성 (시간 역순)
        now = datetime.now()
        message_ids = []
        for i in range(10):
            message_id = uuid7()
            model = ChatMessageModel(
                message_id=message_id,
                room_id=sample_room.room_id,
                user_id=sample_user.user_id,
                content=f"메시지 {i}",
                message_type=MessageType.TEXT.value,
                is_system=False,
                expires_at=now + timedelta(days=3),
                created_at=now + timedelta(seconds=i),
                updated_at=now + timedelta(seconds=i),
            )
            test_session.add(model)
            message_ids.append(message_id)
        await test_session.flush()

        # When: 처음 5개 조회
        messages = await chat_message_repository.find_by_room_id_paginated(
            room_id=Id(str(sample_room.room_id)),
            cursor=None,
            limit=5,
        )

        # Then: 최신 5개 반환 (created_at DESC)
        assert len(messages) == 5
        assert messages[0].content.value == "메시지 9"  # 최신
        assert messages[4].content.value == "메시지 5"

        # When: cursor로 다음 5개 조회
        cursor = messages[4].message_id
        next_messages = await chat_message_repository.find_by_room_id_paginated(
            room_id=Id(str(sample_room.room_id)),
            cursor=cursor,
            limit=5,
        )

        # Then: 다음 5개 반환
        assert len(next_messages) == 5
        assert next_messages[0].content.value == "메시지 4"
        assert next_messages[4].content.value == "메시지 0"

    async def test_find_by_room_id_empty(
        self,
        chat_message_repository: SqlAlchemyChatMessageRepository,
        sample_room: RoomModel,
    ):
        """빈 룸의 메시지 조회 테스트."""
        # When: 메시지가 없는 룸 조회
        messages = await chat_message_repository.find_by_room_id_paginated(
            room_id=Id(str(sample_room.room_id)),
        )

        # Then: 빈 리스트 반환
        assert len(messages) == 0
