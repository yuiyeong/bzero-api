from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from uuid_utils import uuid7

from bzero.domain.entities.room_stay import RoomStay
from bzero.domain.errors import NotFoundRoomStayError
from bzero.domain.value_objects import Id, RoomStayStatus
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.room_model import RoomModel
from bzero.infrastructure.db.room_stay_model import RoomStayModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.room_stay import (
    SqlAlchemyRoomStayRepository,
    SqlAlchemyRoomStaySyncRepository,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def room_stay_repository(test_session: AsyncSession) -> SqlAlchemyRoomStayRepository:
    """RoomStayRepository fixture를 생성합니다."""
    return SqlAlchemyRoomStayRepository(test_session)


@pytest.fixture
def room_stay_sync_repository(test_sync_session: Session) -> SqlAlchemyRoomStaySyncRepository:
    """RoomStaySyncRepository fixture를 생성합니다."""
    return SqlAlchemyRoomStaySyncRepository(test_sync_session)


@pytest.fixture
async def sample_user(test_session: AsyncSession) -> UserModel:
    """테스트용 샘플 유저 데이터를 생성합니다."""
    now = datetime.now()
    user = UserModel(
        user_id=uuid7(),
        email="test@example.com",
        nickname="테스트유저",
        profile_emoji="👤",
        current_points=10000,
        created_at=now,
        updated_at=now,
    )
    test_session.add(user)
    await test_session.flush()
    return user


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
        guest_house_type="mixed",
        name="혼합형 게스트하우스",
        description="대화를 나눌 수 있는 공간",
        image_url="https://example.com/mixed.jpg",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(guest_house)
    await test_session.flush()
    return guest_house


@pytest.fixture
async def sample_room(test_session: AsyncSession, sample_guest_house: GuestHouseModel) -> RoomModel:
    """테스트용 샘플 룸 데이터를 생성합니다."""
    now = datetime.now()
    room = RoomModel(
        room_id=uuid7(),
        guest_house_id=sample_guest_house.guest_house_id,
        max_capacity=6,
        current_capacity=0,
        created_at=now,
        updated_at=now,
    )
    test_session.add(room)
    await test_session.flush()
    return room


@pytest.fixture
async def sample_airship(test_session: AsyncSession) -> AirshipModel:
    """테스트용 샘플 비행선 데이터를 생성합니다."""
    now = datetime.now()
    airship = AirshipModel(
        airship_id=uuid7(),
        name="일반 비행선",
        description="편안하고 여유로운 여행을 원하는 여행자를 위한 비행선",
        image_url="https://example.com/normal.jpg",
        cost_factor=1,
        duration_factor=1,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(airship)
    await test_session.flush()
    return airship


@pytest.fixture
async def sample_ticket(
    test_session: AsyncSession,
    sample_user: UserModel,
    sample_city: CityModel,
    sample_airship: AirshipModel,
) -> TicketModel:
    """테스트용 샘플 티켓 데이터를 생성합니다."""
    now = datetime.now()
    ticket = TicketModel(
        ticket_id=uuid7(),
        user_id=sample_user.user_id,
        city_id=sample_city.city_id,
        city_name=sample_city.name,
        city_theme=sample_city.theme,
        city_description=sample_city.description,
        city_image_url=sample_city.image_url,
        city_base_cost_points=sample_city.base_cost_points,
        city_base_duration_hours=sample_city.base_duration_hours,
        airship_id=sample_airship.airship_id,
        airship_name=sample_airship.name,
        airship_description=sample_airship.description,
        airship_image_url=sample_airship.image_url,
        airship_cost_factor=sample_airship.cost_factor,
        airship_duration_factor=sample_airship.duration_factor,
        ticket_number="B0-2025-TEST001",
        cost_points=300,
        status="completed",
        departure_datetime=now - timedelta(hours=24),
        arrival_datetime=now,
        created_at=now - timedelta(hours=24),
        updated_at=now,
    )
    test_session.add(ticket)
    await test_session.flush()
    return ticket


@pytest.fixture
async def sample_room_stays(
    test_session: AsyncSession,
    sample_user: UserModel,
    sample_city: CityModel,
    sample_guest_house: GuestHouseModel,
    sample_room: RoomModel,
    sample_ticket: TicketModel,
) -> list[RoomStayModel]:
    """테스트용 샘플 룸 스테이 데이터를 생성합니다."""
    now = datetime.now()
    room_stays = [
        # CHECKED_IN 상태
        RoomStayModel(
            room_stay_id=uuid7(),
            user_id=sample_user.user_id,
            city_id=sample_city.city_id,
            guest_house_id=sample_guest_house.guest_house_id,
            room_id=sample_room.room_id,
            ticket_id=sample_ticket.ticket_id,
            status=RoomStayStatus.CHECKED_IN.value,
            check_in_at=now - timedelta(hours=1),
            scheduled_check_out_at=now + timedelta(hours=23),
            actual_check_out_at=None,
            extension_count=0,
            created_at=now - timedelta(hours=1),
            updated_at=now - timedelta(hours=1),
        ),
        # CHECKED_OUT 상태
        RoomStayModel(
            room_stay_id=uuid7(),
            user_id=sample_user.user_id,
            city_id=sample_city.city_id,
            guest_house_id=sample_guest_house.guest_house_id,
            room_id=sample_room.room_id,
            ticket_id=sample_ticket.ticket_id,
            status=RoomStayStatus.CHECKED_OUT.value,
            check_in_at=now - timedelta(days=2),
            scheduled_check_out_at=now - timedelta(days=1),
            actual_check_out_at=now - timedelta(days=1),
            extension_count=0,
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(days=1),
        ),
        # EXTENDED 상태
        RoomStayModel(
            room_stay_id=uuid7(),
            user_id=sample_user.user_id,
            city_id=sample_city.city_id,
            guest_house_id=sample_guest_house.guest_house_id,
            room_id=sample_room.room_id,
            ticket_id=sample_ticket.ticket_id,
            status=RoomStayStatus.EXTENDED.value,
            check_in_at=now - timedelta(hours=12),
            scheduled_check_out_at=now + timedelta(hours=36),
            actual_check_out_at=None,
            extension_count=1,
            created_at=now - timedelta(hours=12),
            updated_at=now,
        ),
    ]

    test_session.add_all(room_stays)
    await test_session.flush()
    return room_stays


# 동기 버전 fixtures
@pytest.fixture
def sample_user_sync(test_sync_session: Session) -> UserModel:
    """테스트용 샘플 유저 데이터를 생성합니다 (동기)."""
    now = datetime.now()
    user = UserModel(
        user_id=str(uuid7()),
        email="sync@example.com",
        nickname="동기유저",
        profile_emoji="🔄",
        current_points=10000,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(user)
    test_sync_session.flush()
    return user


@pytest.fixture
def sample_city_sync(test_sync_session: Session) -> CityModel:
    """테스트용 샘플 도시 데이터를 생성합니다 (동기)."""
    now = datetime.now()
    city = CityModel(
        city_id=str(uuid7()),
        name="로렌시아",
        theme="회복",
        description="숲 속 오두막",
        image_url="https://example.com/lorensia.jpg",
        base_cost_points=300,
        base_duration_hours=24,
        is_active=True,
        display_order=2,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(city)
    test_sync_session.flush()
    return city


@pytest.fixture
def sample_guest_house_sync(test_sync_session: Session, sample_city_sync: CityModel) -> GuestHouseModel:
    """테스트용 샘플 게스트하우스 데이터를 생성합니다 (동기)."""
    now = datetime.now()
    guest_house = GuestHouseModel(
        guest_house_id=str(uuid7()),
        city_id=sample_city_sync.city_id,
        guest_house_type="quiet",
        name="조용한 게스트하우스",
        description="조용히 쉴 수 있는 공간",
        image_url="https://example.com/quiet.jpg",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(guest_house)
    test_sync_session.flush()
    return guest_house


@pytest.fixture
def sample_room_sync(test_sync_session: Session, sample_guest_house_sync: GuestHouseModel) -> RoomModel:
    """테스트용 샘플 룸 데이터를 생성합니다 (동기)."""
    now = datetime.now()
    room = RoomModel(
        room_id=str(uuid7()),
        guest_house_id=sample_guest_house_sync.guest_house_id,
        max_capacity=6,
        current_capacity=0,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(room)
    test_sync_session.flush()
    return room


@pytest.fixture
def sample_airship_sync(test_sync_session: Session) -> AirshipModel:
    """테스트용 샘플 비행선 데이터를 생성합니다 (동기)."""
    now = datetime.now()
    airship = AirshipModel(
        airship_id=str(uuid7()),
        name="쾌속 비행선",
        description="빠르게 이동하는 비행선",
        image_url="https://example.com/express.jpg",
        cost_factor=1.5,
        duration_factor=0.5,
        display_order=2,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(airship)
    test_sync_session.flush()
    return airship


@pytest.fixture
def sample_ticket_sync(
    test_sync_session: Session,
    sample_user_sync: UserModel,
    sample_city_sync: CityModel,
    sample_airship_sync: AirshipModel,
) -> TicketModel:
    """테스트용 샘플 티켓 데이터를 생성합니다 (동기)."""
    now = datetime.now()
    ticket = TicketModel(
        ticket_id=str(uuid7()),
        user_id=sample_user_sync.user_id,
        city_id=sample_city_sync.city_id,
        city_name=sample_city_sync.name,
        city_theme=sample_city_sync.theme,
        city_description=sample_city_sync.description,
        city_image_url=sample_city_sync.image_url,
        city_base_cost_points=sample_city_sync.base_cost_points,
        city_base_duration_hours=sample_city_sync.base_duration_hours,
        airship_id=sample_airship_sync.airship_id,
        airship_name=sample_airship_sync.name,
        airship_description=sample_airship_sync.description,
        airship_image_url=sample_airship_sync.image_url,
        airship_cost_factor=sample_airship_sync.cost_factor,
        airship_duration_factor=sample_airship_sync.duration_factor,
        ticket_number="B0-2025-TEST002",
        cost_points=450,
        status="completed",
        departure_datetime=now - timedelta(hours=12),
        arrival_datetime=now,
        created_at=now - timedelta(hours=12),
        updated_at=now,
    )
    test_sync_session.add(ticket)
    test_sync_session.flush()
    return ticket


# =============================================================================
# 비동기 Repository 테스트
# =============================================================================


class TestRoomStayRepositoryCreate:
    """RoomStayRepository.create() 메서드 테스트."""

    async def test_create_room_stay_success(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
        sample_user: UserModel,
        sample_city: CityModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_ticket: TicketModel,
    ):
        """새로운 룸 스테이를 생성할 수 있어야 합니다."""
        # Given
        now = datetime.now()
        room_stay = RoomStay.create(
            user_id=Id(str(sample_user.user_id)),
            city_id=Id(str(sample_city.city_id)),
            guest_house_id=Id(str(sample_guest_house.guest_house_id)),
            room_id=Id(str(sample_room.room_id)),
            ticket_id=Id(str(sample_ticket.ticket_id)),
            check_in_at=now,
            scheduled_check_out_at=now + timedelta(hours=24),
            created_at=now,
            updated_at=now,
        )

        # When
        created = await room_stay_repository.create(room_stay)

        # Then
        assert created is not None
        assert str(created.room_stay_id.value) == str(room_stay.room_stay_id.value)
        assert str(created.user_id.value) == str(sample_user.user_id)
        assert str(created.city_id.value) == str(sample_city.city_id)
        assert str(created.guest_house_id.value) == str(sample_guest_house.guest_house_id)
        assert str(created.room_id.value) == str(sample_room.room_id)
        assert str(created.ticket_id.value) == str(sample_ticket.ticket_id)
        assert created.status == RoomStayStatus.CHECKED_IN
        assert created.extension_count == 0
        assert created.actual_check_out_at is None


class TestRoomStayRepositoryFindByRoomStayId:
    """RoomStayRepository.find_by_room_stay_id() 메서드 테스트."""

    async def test_find_by_room_stay_id_success(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
        sample_room_stays: list[RoomStayModel],
    ):
        """ID로 룸 스테이를 조회할 수 있어야 합니다."""
        # Given
        room_stay_model = sample_room_stays[0]

        # When
        room_stay = await room_stay_repository.find_by_room_stay_id(Id(str(room_stay_model.room_stay_id)))

        # Then
        assert room_stay is not None
        assert str(room_stay.room_stay_id.value) == str(room_stay_model.room_stay_id)
        assert room_stay.status == RoomStayStatus.CHECKED_IN

    async def test_find_by_room_stay_id_returns_none_when_not_found(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
    ):
        """존재하지 않는 ID로 조회 시 None을 반환해야 합니다."""
        # Given: 존재하지 않는 ID
        non_existent_id = Id()

        # When
        room_stay = await room_stay_repository.find_by_room_stay_id(non_existent_id)

        # Then
        assert room_stay is None

    async def test_find_by_room_stay_id_soft_deleted_excluded(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
        sample_room_stays: list[RoomStayModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 룸 스테이는 조회되지 않아야 합니다."""
        # Given: 룸 스테이를 soft delete
        room_stay_model = sample_room_stays[0]
        room_stay_model.deleted_at = datetime.now()
        await test_session.flush()

        # When
        room_stay = await room_stay_repository.find_by_room_stay_id(Id(str(room_stay_model.room_stay_id)))

        # Then
        assert room_stay is None


class TestRoomStayRepositoryFindCheckedInByUserId:
    """RoomStayRepository.find_checked_in_by_user_id() 메서드 테스트."""

    async def test_find_checked_in_by_user_id_success(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
        test_session: AsyncSession,
        sample_user: UserModel,
        sample_room_stays: list[RoomStayModel],
    ):
        """사용자의 체크인된 룸 스테이를 조회할 수 있어야 합니다."""
        # Given: EXTENDED 상태를 CHECKED_OUT으로 변경하여 CHECKED_IN만 남김
        extended_room_stay = sample_room_stays[2]  # EXTENDED 상태
        extended_room_stay.status = RoomStayStatus.CHECKED_OUT.value
        extended_room_stay.actual_check_out_at = datetime.now()
        await test_session.flush()

        # When
        room_stay = await room_stay_repository.find_checked_in_by_user_id(Id(str(sample_user.user_id)))

        # Then
        assert room_stay is not None
        assert str(room_stay.user_id.value) == str(sample_user.user_id)
        assert room_stay.status == RoomStayStatus.CHECKED_IN

    async def test_find_checked_in_by_user_id_returns_extended_status(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
        test_session: AsyncSession,
        sample_user: UserModel,
        sample_room_stays: list[RoomStayModel],
    ):
        """EXTENDED 상태인 룸 스테이도 조회되어야 합니다."""
        # Given: CHECKED_IN과 EXTENDED 상태를 모두 CHECKED_OUT으로 변경
        for room_stay in sample_room_stays[:2]:  # CHECKED_IN과 CHECKED_OUT
            room_stay.status = RoomStayStatus.CHECKED_OUT.value
            room_stay.actual_check_out_at = datetime.now()
        await test_session.flush()

        # When: EXTENDED 상태만 남음
        room_stay = await room_stay_repository.find_checked_in_by_user_id(Id(str(sample_user.user_id)))

        # Then: EXTENDED 상태가 조회됨
        assert room_stay is not None
        assert str(room_stay.user_id.value) == str(sample_user.user_id)
        assert room_stay.status == RoomStayStatus.EXTENDED

    async def test_find_checked_in_by_user_id_returns_none_when_no_checked_in(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
        test_session: AsyncSession,
        sample_room_stays: list[RoomStayModel],
    ):
        """체크인된 룸 스테이가 없으면 None을 반환해야 합니다."""
        # Given: 모든 룸 스테이를 CHECKED_OUT으로 변경
        for room_stay in sample_room_stays:
            room_stay.status = RoomStayStatus.CHECKED_OUT.value
            room_stay.actual_check_out_at = datetime.now()
        await test_session.flush()

        # When
        room_stay = await room_stay_repository.find_checked_in_by_user_id(Id(str(sample_room_stays[0].user_id)))

        # Then
        assert room_stay is None


class TestRoomStayRepositoryFindAllCheckedInByRoomId:
    """RoomStayRepository.find_all_checked_in_by_room_id() 메서드 테스트."""

    async def test_find_all_checked_in_by_room_id_success(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
        sample_room: RoomModel,
        sample_room_stays: list[RoomStayModel],
    ):
        """룸의 체크인된 모든 룸 스테이를 조회할 수 있어야 합니다."""
        # When
        room_stays = await room_stay_repository.find_all_checked_in_by_room_id(Id(str(sample_room.room_id)))

        # Then: CHECKED_IN, EXTENDED 상태 2개 조회됨 (CHECKED_OUT 제외)
        assert len(room_stays) == 2
        assert all(rs.status in (RoomStayStatus.CHECKED_IN, RoomStayStatus.EXTENDED) for rs in room_stays)
        assert all(rs.status != RoomStayStatus.CHECKED_OUT for rs in room_stays)

    async def test_find_all_checked_in_by_room_id_empty_when_no_checked_in(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
        test_session: AsyncSession,
        sample_room: RoomModel,
        sample_room_stays: list[RoomStayModel],
    ):
        """체크인된 룸 스테이가 없으면 빈 리스트를 반환해야 합니다."""
        # Given: 모든 룸 스테이를 CHECKED_OUT으로 변경
        for room_stay in sample_room_stays:
            room_stay.status = RoomStayStatus.CHECKED_OUT.value
            room_stay.actual_check_out_at = datetime.now()
        await test_session.flush()

        # When
        room_stays = await room_stay_repository.find_all_checked_in_by_room_id(Id(str(sample_room.room_id)))

        # Then
        assert room_stays == []


class TestRoomStayRepositoryFindAllByTicketId:
    """RoomStayRepository.find_all_by_ticket_id() 메서드 테스트."""

    async def test_find_all_by_ticket_id_success(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
        sample_ticket: TicketModel,
        sample_room_stays: list[RoomStayModel],
    ):
        """티켓 ID로 모든 룸 스테이를 조회할 수 있어야 합니다."""
        # When
        room_stays = await room_stay_repository.find_all_by_ticket_id(Id(str(sample_ticket.ticket_id)))

        # Then: 3개 모두 조회됨
        assert len(room_stays) == 3
        assert all(str(rs.ticket_id.value) == str(sample_ticket.ticket_id) for rs in room_stays)

    async def test_find_all_by_ticket_id_empty_when_no_results(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
    ):
        """티켓에 연결된 룸 스테이가 없으면 빈 리스트를 반환해야 합니다."""
        # Given: 존재하지 않는 티켓 ID
        non_existent_ticket_id = Id()

        # When
        room_stays = await room_stay_repository.find_all_by_ticket_id(non_existent_ticket_id)

        # Then
        assert room_stays == []


class TestRoomStayRepositoryFindAllDueForCheckOut:
    """RoomStayRepository.find_all_due_for_check_out() 메서드 테스트."""

    async def test_find_all_due_for_check_out_success(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
        test_session: AsyncSession,
        sample_user: UserModel,
        sample_city: CityModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_ticket: TicketModel,
    ):
        """체크아웃 예정 시간이 지난 룸 스테이를 조회할 수 있어야 합니다."""
        # Given: 체크아웃 예정 시간이 지난 룸 스테이 생성
        now = datetime.now(tz=UTC)
        room_stay_model = RoomStayModel(
            room_stay_id=uuid7(),
            user_id=sample_user.user_id,
            city_id=sample_city.city_id,
            guest_house_id=sample_guest_house.guest_house_id,
            room_id=sample_room.room_id,
            ticket_id=sample_ticket.ticket_id,
            status=RoomStayStatus.CHECKED_IN.value,
            check_in_at=now - timedelta(hours=25),
            scheduled_check_out_at=now - timedelta(hours=1),  # 1시간 전
            actual_check_out_at=None,
            extension_count=0,
            created_at=now - timedelta(hours=25),
            updated_at=now - timedelta(hours=25),
        )
        test_session.add(room_stay_model)
        await test_session.flush()

        # When
        room_stays = await room_stay_repository.find_all_due_for_check_out(before=now)

        # Then: 체크아웃 예정 시간이 지난 룸 스테이만 조회됨
        assert len(room_stays) >= 1
        assert all(rs.status in (RoomStayStatus.CHECKED_IN, RoomStayStatus.EXTENDED) for rs in room_stays)
        assert all(rs.status != RoomStayStatus.CHECKED_OUT for rs in room_stays)

    async def test_find_all_due_for_check_out_includes_extended_status(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
        test_session: AsyncSession,
        sample_user: UserModel,
        sample_city: CityModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_ticket: TicketModel,
    ):
        """체크아웃 예정 시간이 지난 EXTENDED 상태 룸 스테이도 조회되어야 합니다."""
        # Given: 체크아웃 예정 시간이 지난 EXTENDED 상태 룸 스테이 생성
        now = datetime.now(tz=UTC)
        room_stay_model = RoomStayModel(
            room_stay_id=uuid7(),
            user_id=sample_user.user_id,
            city_id=sample_city.city_id,
            guest_house_id=sample_guest_house.guest_house_id,
            room_id=sample_room.room_id,
            ticket_id=sample_ticket.ticket_id,
            status=RoomStayStatus.EXTENDED.value,
            check_in_at=now - timedelta(hours=25),
            scheduled_check_out_at=now - timedelta(hours=1),  # 1시간 전
            actual_check_out_at=None,
            extension_count=1,
            created_at=now - timedelta(hours=25),
            updated_at=now,
        )
        test_session.add(room_stay_model)
        await test_session.flush()

        # When
        room_stays = await room_stay_repository.find_all_due_for_check_out(before=now)

        # Then: EXTENDED 상태도 조회됨
        extended_stays = [rs for rs in room_stays if rs.status == RoomStayStatus.EXTENDED]
        assert len(extended_stays) >= 1

    async def test_find_all_due_for_check_out_empty_when_no_results(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
        sample_room_stays: list[RoomStayModel],
    ):
        """체크아웃 예정 시간이 지난 룸 스테이가 없으면 빈 리스트를 반환해야 합니다."""
        # Given: 현재 시간보다 과거 시간으로 조회
        past = datetime.now() - timedelta(days=10)

        # When
        room_stays = await room_stay_repository.find_all_due_for_check_out(before=past)

        # Then
        assert room_stays == []


class TestRoomStayRepositoryUpdate:
    """RoomStayRepository.update() 메서드 테스트."""

    async def test_update_room_stay_status_success(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
        sample_room_stays: list[RoomStayModel],
    ):
        """룸 스테이 상태를 업데이트할 수 있어야 합니다."""
        # Given: CHECKED_IN 상태인 첫 번째 룸 스테이를 CHECKED_OUT으로 변경
        room_stay_model = sample_room_stays[0]
        room_stay = await room_stay_repository.find_by_room_stay_id(Id(str(room_stay_model.room_stay_id)))
        assert room_stay is not None
        assert room_stay.status == RoomStayStatus.CHECKED_IN

        # When: 상태를 CHECKED_OUT으로 변경
        now = datetime.now(tz=UTC)
        room_stay.status = RoomStayStatus.CHECKED_OUT
        room_stay.actual_check_out_at = now
        updated = await room_stay_repository.update(room_stay)

        # Then
        assert updated is not None
        assert updated.status == RoomStayStatus.CHECKED_OUT
        assert updated.actual_check_out_at is not None
        assert str(updated.room_stay_id.value) == str(room_stay_model.room_stay_id)

    async def test_update_room_stay_extension_count_success(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
        sample_room_stays: list[RoomStayModel],
    ):
        """룸 스테이 연장 횟수를 업데이트할 수 있어야 합니다."""
        # Given
        room_stay_model = sample_room_stays[0]
        room_stay = await room_stay_repository.find_by_room_stay_id(Id(str(room_stay_model.room_stay_id)))
        assert room_stay is not None
        assert room_stay.extension_count == 0

        # When: 연장 횟수 증가
        room_stay.extension_count += 1
        room_stay.status = RoomStayStatus.EXTENDED
        room_stay.scheduled_check_out_at = room_stay.scheduled_check_out_at + timedelta(hours=24)
        updated = await room_stay_repository.update(room_stay)

        # Then
        assert updated is not None
        assert updated.extension_count == 1
        assert updated.status == RoomStayStatus.EXTENDED

    async def test_update_non_existent_room_stay_raises_error(
        self,
        room_stay_repository: SqlAlchemyRoomStayRepository,
        sample_user: UserModel,
        sample_city: CityModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_ticket: TicketModel,
    ):
        """존재하지 않는 룸 스테이 업데이트 시 NotFoundRoomStayError 발생."""
        # Given: 존재하지 않는 룸 스테이 엔티티
        now = datetime.now()
        non_existent_room_stay = RoomStay(
            room_stay_id=Id(),  # 새로운 ID (DB에 없음)
            user_id=Id(str(sample_user.user_id)),
            city_id=Id(str(sample_city.city_id)),
            guest_house_id=Id(str(sample_guest_house.guest_house_id)),
            room_id=Id(str(sample_room.room_id)),
            ticket_id=Id(str(sample_ticket.ticket_id)),
            status=RoomStayStatus.CHECKED_IN,
            check_in_at=now,
            scheduled_check_out_at=now + timedelta(hours=24),
            actual_check_out_at=None,
            extension_count=0,
            created_at=now,
            updated_at=now,
        )

        # When/Then: NotFoundRoomStayError 발생
        with pytest.raises(NotFoundRoomStayError):
            await room_stay_repository.update(non_existent_room_stay)


# =============================================================================
# 동기 Repository 테스트
# =============================================================================


class TestRoomStaySyncRepositoryCreate:
    """RoomStaySyncRepository.create() 메서드 테스트 (동기)."""

    def test_create_room_stay_success(
        self,
        room_stay_sync_repository: SqlAlchemyRoomStaySyncRepository,
        sample_user_sync: UserModel,
        sample_city_sync: CityModel,
        sample_guest_house_sync: GuestHouseModel,
        sample_room_sync: RoomModel,
        sample_ticket_sync: TicketModel,
    ):
        """새로운 룸 스테이를 생성할 수 있어야 합니다 (동기)."""
        # Given
        now = datetime.now()
        room_stay = RoomStay.create(
            user_id=Id(str(sample_user_sync.user_id)),
            city_id=Id(str(sample_city_sync.city_id)),
            guest_house_id=Id(str(sample_guest_house_sync.guest_house_id)),
            room_id=Id(str(sample_room_sync.room_id)),
            ticket_id=Id(str(sample_ticket_sync.ticket_id)),
            check_in_at=now,
            scheduled_check_out_at=now + timedelta(hours=24),
            created_at=now,
            updated_at=now,
        )

        # When
        created = room_stay_sync_repository.create(room_stay)

        # Then
        assert created is not None
        assert str(created.room_stay_id.value) == str(room_stay.room_stay_id.value)
        assert str(created.user_id.value) == str(sample_user_sync.user_id)
        assert created.status == RoomStayStatus.CHECKED_IN


class TestRoomStaySyncRepositoryFindByRoomStayId:
    """RoomStaySyncRepository.find_by_room_stay_id() 메서드 테스트 (동기)."""

    def test_find_by_room_stay_id_success(
        self,
        room_stay_sync_repository: SqlAlchemyRoomStaySyncRepository,
        test_sync_session: Session,
        sample_user_sync: UserModel,
        sample_city_sync: CityModel,
        sample_guest_house_sync: GuestHouseModel,
        sample_room_sync: RoomModel,
        sample_ticket_sync: TicketModel,
    ):
        """ID로 룸 스테이를 조회할 수 있어야 합니다 (동기)."""
        # Given
        now = datetime.now()
        room_stay_model = RoomStayModel(
            room_stay_id=str(uuid7()),
            user_id=sample_user_sync.user_id,
            city_id=sample_city_sync.city_id,
            guest_house_id=sample_guest_house_sync.guest_house_id,
            room_id=sample_room_sync.room_id,
            ticket_id=sample_ticket_sync.ticket_id,
            status=RoomStayStatus.CHECKED_IN.value,
            check_in_at=now,
            scheduled_check_out_at=now + timedelta(hours=24),
            actual_check_out_at=None,
            extension_count=0,
            created_at=now,
            updated_at=now,
        )
        test_sync_session.add(room_stay_model)
        test_sync_session.flush()

        # When
        room_stay = room_stay_sync_repository.find_by_room_stay_id(Id(str(room_stay_model.room_stay_id)))

        # Then
        assert room_stay is not None
        assert str(room_stay.room_stay_id.value) == str(room_stay_model.room_stay_id)


class TestRoomStaySyncRepositoryUpdate:
    """RoomStaySyncRepository.update() 메서드 테스트 (동기)."""

    def test_update_room_stay_status_success(
        self,
        room_stay_sync_repository: SqlAlchemyRoomStaySyncRepository,
        test_sync_session: Session,
        sample_user_sync: UserModel,
        sample_city_sync: CityModel,
        sample_guest_house_sync: GuestHouseModel,
        sample_room_sync: RoomModel,
        sample_ticket_sync: TicketModel,
    ):
        """룸 스테이 상태를 업데이트할 수 있어야 합니다 (동기)."""
        # Given
        now = datetime.now(tz=UTC)
        room_stay_model = RoomStayModel(
            room_stay_id=str(uuid7()),
            user_id=sample_user_sync.user_id,
            city_id=sample_city_sync.city_id,
            guest_house_id=sample_guest_house_sync.guest_house_id,
            room_id=sample_room_sync.room_id,
            ticket_id=sample_ticket_sync.ticket_id,
            status=RoomStayStatus.CHECKED_IN.value,
            check_in_at=now,
            scheduled_check_out_at=now + timedelta(hours=24),
            actual_check_out_at=None,
            extension_count=0,
            created_at=now,
            updated_at=now,
        )
        test_sync_session.add(room_stay_model)
        test_sync_session.flush()

        room_stay = room_stay_sync_repository.find_by_room_stay_id(Id(str(room_stay_model.room_stay_id)))
        assert room_stay is not None

        # When: 상태를 CHECKED_OUT으로 변경
        room_stay.status = RoomStayStatus.CHECKED_OUT
        room_stay.actual_check_out_at = now
        updated = room_stay_sync_repository.update(room_stay)

        # Then
        assert updated is not None
        assert updated.status == RoomStayStatus.CHECKED_OUT
        assert updated.actual_check_out_at is not None
