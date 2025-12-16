from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from uuid_utils import uuid7

from bzero.domain.entities.room import Room
from bzero.domain.errors import NotFoundRoomError
from bzero.domain.value_objects import GuestHouseType, Id
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.room_model import RoomModel
from bzero.infrastructure.repositories.room import SqlAlchemyRoomRepository, SqlAlchemyRoomSyncRepository


@pytest.fixture
async def sample_city(test_session: AsyncSession) -> CityModel:
    """테스트용 샘플 도시 데이터를 생성합니다."""
    now = datetime.now()
    city = CityModel(
        city_id=uuid7(),
        name="세렌시아",
        theme="관계",
        description="노을빛 항구 마을",
        image_url="https://example.com/serentia.jpg",
        base_cost_points=300,
        base_duration_hours=24,
        is_active=True,
        display_order=1,
        created_at=now,
        updated_at=now,
    )
    test_session.add(city)
    await test_session.flush()
    return city


@pytest.fixture
async def sample_guest_house(test_session: AsyncSession, sample_city: CityModel) -> GuestHouseModel:
    """테스트용 샘플 게스트하우스 데이터를 생성합니다."""
    now = datetime.now()
    guest_house = GuestHouseModel(
        guest_house_id=uuid7(),
        city_id=sample_city.city_id,
        guest_house_type=GuestHouseType.MIXED.value,
        name="세렌시아 게스트하우스",
        description="노을빛 항구 마을의 따뜻한 게스트하우스",
        image_url="https://example.com/guesthouse.jpg",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(guest_house)
    await test_session.flush()
    return guest_house


@pytest.fixture
def sample_city_sync(test_sync_session: Session) -> CityModel:
    """테스트용 동기 샘플 도시 데이터를 생성합니다."""
    now = datetime.now()
    city = CityModel(
        city_id=str(uuid7()),
        name="세렌시아",
        theme="관계",
        description="노을빛 항구 마을",
        image_url="https://example.com/serentia.jpg",
        base_cost_points=300,
        base_duration_hours=24,
        is_active=True,
        display_order=1,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(city)
    test_sync_session.flush()
    return city


@pytest.fixture
def sample_guest_house_sync(test_sync_session: Session, sample_city_sync: CityModel) -> GuestHouseModel:
    """테스트용 동기 샘플 게스트하우스 데이터를 생성합니다."""
    now = datetime.now()
    guest_house = GuestHouseModel(
        guest_house_id=str(uuid7()),
        city_id=sample_city_sync.city_id,
        guest_house_type=GuestHouseType.MIXED.value,
        name="세렌시아 게스트하우스",
        description="노을빛 항구 마을의 따뜻한 게스트하우스",
        image_url="https://example.com/guesthouse.jpg",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(guest_house)
    test_sync_session.flush()
    return guest_house


# =============================================================================
# 비동기 리포지토리 테스트 (SqlAlchemyRoomRepository)
# =============================================================================


@pytest.fixture
def room_repository(test_session: AsyncSession) -> SqlAlchemyRoomRepository:
    """RoomRepository fixture를 생성합니다."""
    return SqlAlchemyRoomRepository(test_session)


class TestRoomRepositoryCreate:
    """RoomRepository.create() 메서드 테스트."""

    async def test_create_room_success(
        self,
        room_repository: SqlAlchemyRoomRepository,
        sample_guest_house: GuestHouseModel,
    ):
        """새로운 룸을 생성할 수 있어야 합니다."""
        # Given
        now = datetime.now()
        room = Room.create(
            guest_house_id=Id(str(sample_guest_house.guest_house_id)),
            max_capacity=6,
            created_at=now,
            updated_at=now,
        )

        # When
        created = await room_repository.create(room)

        # Then
        assert created is not None
        assert str(created.room_id.value) == str(room.room_id.value)
        assert str(created.guest_house_id.value) == str(sample_guest_house.guest_house_id)
        assert created.max_capacity == 6
        assert created.current_capacity == 0
        assert created.is_empty is True
        assert created.is_full is False


class TestRoomRepositoryFindByRoomId:
    """RoomRepository.find_by_room_id() 메서드 테스트."""

    async def test_find_by_room_id_success(
        self,
        room_repository: SqlAlchemyRoomRepository,
        sample_guest_house: GuestHouseModel,
        test_session: AsyncSession,
    ):
        """ID로 룸을 조회할 수 있어야 합니다."""
        # Given: 룸을 미리 생성
        now = datetime.now()
        room_model = RoomModel(
            room_id=uuid7(),
            guest_house_id=sample_guest_house.guest_house_id,
            max_capacity=6,
            current_capacity=3,
            created_at=now,
            updated_at=now,
        )
        test_session.add(room_model)
        await test_session.flush()

        # When
        room = await room_repository.find_by_room_id(Id(str(room_model.room_id)))

        # Then
        assert room is not None
        assert str(room.room_id.value) == str(room_model.room_id)
        assert str(room.guest_house_id.value) == str(sample_guest_house.guest_house_id)
        assert room.max_capacity == 6
        assert room.current_capacity == 3

    async def test_find_by_room_id_returns_none_when_not_found(
        self,
        room_repository: SqlAlchemyRoomRepository,
    ):
        """존재하지 않는 ID로 조회 시 None을 반환해야 합니다."""
        # Given: 존재하지 않는 ID
        non_existent_id = Id()

        # When
        room = await room_repository.find_by_room_id(non_existent_id)

        # Then
        assert room is None

    async def test_find_by_room_id_soft_deleted_excluded(
        self,
        room_repository: SqlAlchemyRoomRepository,
        sample_guest_house: GuestHouseModel,
        test_session: AsyncSession,
    ):
        """Soft delete된 룸은 조회되지 않아야 합니다."""
        # Given: 룸을 soft delete
        now = datetime.now()
        room_model = RoomModel(
            room_id=uuid7(),
            guest_house_id=sample_guest_house.guest_house_id,
            max_capacity=6,
            current_capacity=0,
            created_at=now,
            updated_at=now,
            deleted_at=now,
        )
        test_session.add(room_model)
        await test_session.flush()

        # When
        room = await room_repository.find_by_room_id(Id(str(room_model.room_id)))

        # Then
        assert room is None


class TestRoomRepositoryFindAvailableByGuestHouseIdForUpdate:
    """RoomRepository.find_available_by_guest_house_id_for_update() 메서드 테스트."""

    async def test_find_available_by_guest_house_id_for_update_returns_one_available_room(
        self,
        room_repository: SqlAlchemyRoomRepository,
        sample_guest_house: GuestHouseModel,
        test_session: AsyncSession,
    ):
        """이용 가능한 룸 1개를 조회할 수 있어야 합니다 (FOR UPDATE with LIMIT 1)."""
        # Given: 3개의 룸 생성 (2개는 이용 가능, 1개는 만실)
        now = datetime.now()
        rooms = [
            RoomModel(
                room_id=uuid7(),
                guest_house_id=sample_guest_house.guest_house_id,
                max_capacity=6,
                current_capacity=3,  # 이용 가능
                created_at=now,
                updated_at=now,
            ),
            RoomModel(
                room_id=uuid7(),
                guest_house_id=sample_guest_house.guest_house_id,
                max_capacity=6,
                current_capacity=6,  # 만실
                created_at=now,
                updated_at=now,
            ),
            RoomModel(
                room_id=uuid7(),
                guest_house_id=sample_guest_house.guest_house_id,
                max_capacity=6,
                current_capacity=0,  # 이용 가능
                created_at=now,
                updated_at=now,
            ),
        ]
        for room in rooms:
            test_session.add(room)
        await test_session.flush()

        # When
        available_rooms = await room_repository.find_available_by_guest_house_id_for_update(
            Id(str(sample_guest_house.guest_house_id))
        )

        # Then: LIMIT 1으로 1개만 반환
        assert len(available_rooms) == 1
        assert not available_rooms[0].is_full
        assert str(available_rooms[0].guest_house_id.value) == str(sample_guest_house.guest_house_id)

    async def test_find_available_by_guest_house_id_excludes_soft_deleted(
        self,
        room_repository: SqlAlchemyRoomRepository,
        sample_guest_house: GuestHouseModel,
        test_session: AsyncSession,
    ):
        """Soft delete된 룸은 조회되지 않아야 합니다."""
        # Given: 2개의 룸 생성 (1개는 이용 가능, 1개는 이용 가능이지만 soft deleted)
        now = datetime.now()
        rooms = [
            RoomModel(
                room_id=uuid7(),
                guest_house_id=sample_guest_house.guest_house_id,
                max_capacity=6,
                current_capacity=3,
                created_at=now,
                updated_at=now,
            ),
            RoomModel(
                room_id=uuid7(),
                guest_house_id=sample_guest_house.guest_house_id,
                max_capacity=6,
                current_capacity=2,
                created_at=now,
                updated_at=now,
                deleted_at=now,
            ),
        ]
        for room in rooms:
            test_session.add(room)
        await test_session.flush()

        # When
        available_rooms = await room_repository.find_available_by_guest_house_id_for_update(
            Id(str(sample_guest_house.guest_house_id))
        )

        # Then
        assert len(available_rooms) == 1

    async def test_find_available_by_guest_house_id_returns_empty_list_when_no_rooms(
        self,
        room_repository: SqlAlchemyRoomRepository,
        sample_guest_house: GuestHouseModel,
    ):
        """룸이 없으면 빈 리스트를 반환해야 합니다."""
        # When
        available_rooms = await room_repository.find_available_by_guest_house_id_for_update(
            Id(str(sample_guest_house.guest_house_id))
        )

        # Then
        assert available_rooms == []


class TestRoomRepositoryUpdate:
    """RoomRepository.update() 메서드 테스트."""

    async def test_update_room_success(
        self,
        room_repository: SqlAlchemyRoomRepository,
        sample_guest_house: GuestHouseModel,
        test_session: AsyncSession,
    ):
        """룸을 업데이트할 수 있어야 합니다."""
        # Given: 룸을 미리 생성
        now = datetime.now()
        room_model = RoomModel(
            room_id=uuid7(),
            guest_house_id=sample_guest_house.guest_house_id,
            max_capacity=6,
            current_capacity=3,
            created_at=now,
            updated_at=now,
        )
        test_session.add(room_model)
        await test_session.flush()

        # When: current_capacity 증가
        room = await room_repository.find_by_room_id(Id(str(room_model.room_id)))
        assert room is not None
        room.increase_capacity()
        updated = await room_repository.update(room)

        # Then
        assert updated is not None
        assert str(updated.room_id.value) == str(room_model.room_id)
        assert updated.current_capacity == 4

    async def test_update_non_existent_room_raises_error(
        self,
        room_repository: SqlAlchemyRoomRepository,
        sample_guest_house: GuestHouseModel,
    ):
        """존재하지 않는 룸 업데이트 시 NotFoundRoomError 발생."""
        # Given: 존재하지 않는 룸 엔티티
        now = datetime.now()
        non_existent_room = Room(
            room_id=Id(),  # 새로운 ID (DB에 없음)
            guest_house_id=Id(str(sample_guest_house.guest_house_id)),
            max_capacity=6,
            current_capacity=3,
            created_at=now,
            updated_at=now,
        )

        # When/Then: NotFoundRoomError 발생
        with pytest.raises(NotFoundRoomError):
            await room_repository.update(non_existent_room)


# =============================================================================
# 동기 리포지토리 테스트 (SqlAlchemyRoomSyncRepository)
# =============================================================================


@pytest.fixture
def room_sync_repository(test_sync_session: Session) -> SqlAlchemyRoomSyncRepository:
    """RoomSyncRepository fixture를 생성합니다."""
    return SqlAlchemyRoomSyncRepository(test_sync_session)


class TestRoomSyncRepositoryCreate:
    """RoomSyncRepository.create() 메서드 테스트."""

    def test_create_room_success(
        self,
        room_sync_repository: SqlAlchemyRoomSyncRepository,
        sample_guest_house_sync: GuestHouseModel,
    ):
        """새로운 룸을 생성할 수 있어야 합니다."""
        # Given
        now = datetime.now()
        room = Room.create(
            guest_house_id=Id(str(sample_guest_house_sync.guest_house_id)),
            max_capacity=6,
            created_at=now,
            updated_at=now,
        )

        # When
        created = room_sync_repository.create(room)

        # Then
        assert created is not None
        assert str(created.room_id.value) == str(room.room_id.value)
        assert str(created.guest_house_id.value) == str(sample_guest_house_sync.guest_house_id)
        assert created.max_capacity == 6
        assert created.current_capacity == 0


class TestRoomSyncRepositoryFindByRoomId:
    """RoomSyncRepository.find_by_room_id() 메서드 테스트."""

    def test_find_by_room_id_success(
        self,
        room_sync_repository: SqlAlchemyRoomSyncRepository,
        sample_guest_house_sync: GuestHouseModel,
        test_sync_session: Session,
    ):
        """ID로 룸을 조회할 수 있어야 합니다."""
        # Given: 룸을 미리 생성
        now = datetime.now()
        room_model = RoomModel(
            room_id=uuid7(),
            guest_house_id=sample_guest_house_sync.guest_house_id,
            max_capacity=6,
            current_capacity=3,
            created_at=now,
            updated_at=now,
        )
        test_sync_session.add(room_model)
        test_sync_session.flush()

        # When
        room = room_sync_repository.find_by_room_id(Id(str(room_model.room_id)))

        # Then
        assert room is not None
        assert str(room.room_id.value) == str(room_model.room_id)

    def test_find_by_room_id_returns_none_when_not_found(
        self,
        room_sync_repository: SqlAlchemyRoomSyncRepository,
    ):
        """존재하지 않는 ID로 조회 시 None을 반환해야 합니다."""
        # Given: 존재하지 않는 ID
        non_existent_id = Id()

        # When
        room = room_sync_repository.find_by_room_id(non_existent_id)

        # Then
        assert room is None


class TestRoomSyncRepositoryFindAvailableByGuestHouseIdForUpdate:
    """RoomSyncRepository.find_available_by_guest_house_id_for_update() 메서드 테스트."""

    def test_find_available_by_guest_house_id_for_update_returns_one_available_room(
        self,
        room_sync_repository: SqlAlchemyRoomSyncRepository,
        sample_guest_house_sync: GuestHouseModel,
        test_sync_session: Session,
    ):
        """이용 가능한 룸 1개를 조회할 수 있어야 합니다 (FOR UPDATE with LIMIT 1)."""
        # Given: 3개의 룸 생성 (2개는 이용 가능, 1개는 만실)
        now = datetime.now()
        rooms = [
            RoomModel(
                room_id=uuid7(),
                guest_house_id=sample_guest_house_sync.guest_house_id,
                max_capacity=6,
                current_capacity=3,
                created_at=now,
                updated_at=now,
            ),
            RoomModel(
                room_id=uuid7(),
                guest_house_id=sample_guest_house_sync.guest_house_id,
                max_capacity=6,
                current_capacity=6,
                created_at=now,
                updated_at=now,
            ),
            RoomModel(
                room_id=uuid7(),
                guest_house_id=sample_guest_house_sync.guest_house_id,
                max_capacity=6,
                current_capacity=0,
                created_at=now,
                updated_at=now,
            ),
        ]
        for room in rooms:
            test_sync_session.add(room)
        test_sync_session.flush()

        # When
        available_rooms = room_sync_repository.find_available_by_guest_house_id_for_update(
            Id(str(sample_guest_house_sync.guest_house_id))
        )

        # Then: LIMIT 1으로 1개만 반환
        assert len(available_rooms) == 1
        assert not available_rooms[0].is_full


class TestRoomSyncRepositoryUpdate:
    """RoomSyncRepository.update() 메서드 테스트."""

    def test_update_room_success(
        self,
        room_sync_repository: SqlAlchemyRoomSyncRepository,
        sample_guest_house_sync: GuestHouseModel,
        test_sync_session: Session,
    ):
        """룸을 업데이트할 수 있어야 합니다."""
        # Given: 룸을 미리 생성
        now = datetime.now()
        room_model = RoomModel(
            room_id=uuid7(),
            guest_house_id=sample_guest_house_sync.guest_house_id,
            max_capacity=6,
            current_capacity=3,
            created_at=now,
            updated_at=now,
        )
        test_sync_session.add(room_model)
        test_sync_session.flush()

        # When: current_capacity 증가
        room = room_sync_repository.find_by_room_id(Id(str(room_model.room_id)))
        assert room is not None
        room.increase_capacity()
        updated = room_sync_repository.update(room)

        # Then
        assert updated is not None
        assert str(updated.room_id.value) == str(room_model.room_id)
        assert updated.current_capacity == 4

    def test_update_non_existent_room_raises_error(
        self,
        room_sync_repository: SqlAlchemyRoomSyncRepository,
        sample_guest_house_sync: GuestHouseModel,
    ):
        """존재하지 않는 룸 업데이트 시 NotFoundRoomError 발생."""
        # Given: 존재하지 않는 룸 엔티티
        now = datetime.now()
        non_existent_room = Room(
            room_id=Id(),
            guest_house_id=Id(str(sample_guest_house_sync.guest_house_id)),
            max_capacity=6,
            current_capacity=3,
            created_at=now,
            updated_at=now,
        )

        # When/Then: NotFoundRoomError 발생
        with pytest.raises(NotFoundRoomError):
            room_sync_repository.update(non_existent_room)
