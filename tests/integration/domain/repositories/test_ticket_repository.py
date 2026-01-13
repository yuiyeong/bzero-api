"""TicketRepository Integration Tests."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.domain.entities.ticket import Ticket
from bzero.domain.errors import NotFoundTicketError
from bzero.domain.value_objects import AirshipSnapshot, CitySnapshot, Id, TicketStatus
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.ticket import SqlAlchemyTicketRepository


@pytest.fixture
def ticket_repository(test_session: AsyncSession) -> SqlAlchemyTicketRepository:
    """TicketRepository fixture를 생성합니다."""
    return SqlAlchemyTicketRepository(test_session)


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
        base_duration_minutes=24,
        is_active=True,
        display_order=1,
        created_at=now,
        updated_at=now,
    )
    test_session.add(city)
    await test_session.flush()
    return city


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
async def sample_tickets(
    test_session: AsyncSession,
    sample_user: UserModel,
    sample_city: CityModel,
    sample_airship: AirshipModel,
) -> list[TicketModel]:
    """테스트용 샘플 티켓 데이터를 생성합니다."""
    now = datetime.now()
    tickets = [
        TicketModel(
            ticket_id=uuid7(),
            user_id=sample_user.user_id,
            city_id=sample_city.city_id,
            city_name=sample_city.name,
            city_theme=sample_city.theme,
            city_description=sample_city.description,
            city_image_url=sample_city.image_url,
            city_base_cost_points=sample_city.base_cost_points,
            city_base_duration_minutes=sample_city.base_duration_minutes,
            airship_id=sample_airship.airship_id,
            airship_name=sample_airship.name,
            airship_description=sample_airship.description,
            airship_image_url=sample_airship.image_url,
            airship_cost_factor=sample_airship.cost_factor,
            airship_duration_factor=sample_airship.duration_factor,
            ticket_number="B0-2025-TEST001",
            cost_points=300,
            status=TicketStatus.PURCHASED.value,
            departure_datetime=now + timedelta(hours=1),
            arrival_datetime=now + timedelta(hours=25),
            created_at=now,
            updated_at=now,
        ),
        TicketModel(
            ticket_id=uuid7(),
            user_id=sample_user.user_id,
            city_id=sample_city.city_id,
            city_name=sample_city.name,
            city_theme=sample_city.theme,
            city_description=sample_city.description,
            city_image_url=sample_city.image_url,
            city_base_cost_points=sample_city.base_cost_points,
            city_base_duration_minutes=sample_city.base_duration_minutes,
            airship_id=sample_airship.airship_id,
            airship_name=sample_airship.name,
            airship_description=sample_airship.description,
            airship_image_url=sample_airship.image_url,
            airship_cost_factor=sample_airship.cost_factor,
            airship_duration_factor=sample_airship.duration_factor,
            ticket_number="B0-2025-TEST002",
            cost_points=300,
            status=TicketStatus.BOARDING.value,
            departure_datetime=now - timedelta(hours=1),
            arrival_datetime=now + timedelta(hours=23),
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(hours=2),
        ),
        TicketModel(
            ticket_id=uuid7(),
            user_id=sample_user.user_id,
            city_id=sample_city.city_id,
            city_name=sample_city.name,
            city_theme=sample_city.theme,
            city_description=sample_city.description,
            city_image_url=sample_city.image_url,
            city_base_cost_points=sample_city.base_cost_points,
            city_base_duration_minutes=sample_city.base_duration_minutes,
            airship_id=sample_airship.airship_id,
            airship_name=sample_airship.name,
            airship_description=sample_airship.description,
            airship_image_url=sample_airship.image_url,
            airship_cost_factor=sample_airship.cost_factor,
            airship_duration_factor=sample_airship.duration_factor,
            ticket_number="B0-2025-TEST003",
            cost_points=300,
            status=TicketStatus.COMPLETED.value,
            departure_datetime=now - timedelta(days=2),
            arrival_datetime=now - timedelta(days=1),
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(days=1),
        ),
        TicketModel(
            ticket_id=uuid7(),
            user_id=sample_user.user_id,
            city_id=sample_city.city_id,
            city_name=sample_city.name,
            city_theme=sample_city.theme,
            city_description=sample_city.description,
            city_image_url=sample_city.image_url,
            city_base_cost_points=sample_city.base_cost_points,
            city_base_duration_minutes=sample_city.base_duration_minutes,
            airship_id=sample_airship.airship_id,
            airship_name=sample_airship.name,
            airship_description=sample_airship.description,
            airship_image_url=sample_airship.image_url,
            airship_cost_factor=sample_airship.cost_factor,
            airship_duration_factor=sample_airship.duration_factor,
            ticket_number="B0-2025-TEST004",
            cost_points=300,
            status=TicketStatus.CANCELLED.value,
            departure_datetime=now + timedelta(hours=2),
            arrival_datetime=now + timedelta(hours=26),
            created_at=now - timedelta(hours=1),
            updated_at=now,
        ),
    ]

    test_session.add_all(tickets)
    await test_session.flush()
    return tickets


class TestTicketRepositoryCreate:
    """TicketRepository.create() 메서드 테스트."""

    async def test_create_ticket_success(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_user: UserModel,
        sample_city: CityModel,
        sample_airship: AirshipModel,
    ):
        """새로운 티켓을 생성할 수 있어야 합니다."""
        # Given
        now = datetime.now()
        city_snapshot = CitySnapshot(
            city_id=Id(str(sample_city.city_id)),
            name=sample_city.name,
            theme=sample_city.theme,
            image_url=sample_city.image_url,
            description=sample_city.description,
            base_cost_points=sample_city.base_cost_points,
            base_duration_minutes=sample_city.base_duration_minutes,
        )
        airship_snapshot = AirshipSnapshot(
            airship_id=Id(str(sample_airship.airship_id)),
            name=sample_airship.name,
            image_url=sample_airship.image_url,
            description=sample_airship.description,
            cost_factor=sample_airship.cost_factor,
            duration_factor=sample_airship.duration_factor,
        )

        ticket = Ticket.create(
            user_id=Id.from_hex(str(sample_user.user_id)),
            city_snapshot=city_snapshot,
            airship_snapshot=airship_snapshot,
            cost_points=300,
            departure_datetime=now + timedelta(hours=1),
            arrival_datetime=now + timedelta(hours=25),
            created_at=now,
            updated_at=now,
        )

        # When
        created = await ticket_repository.create(ticket)

        # Then
        assert created is not None
        assert str(created.ticket_id.value) == str(ticket.ticket_id.value)
        assert str(created.user_id.value) == str(sample_user.user_id)
        assert created.city_snapshot.name == sample_city.name
        assert created.airship_snapshot.name == sample_airship.name
        assert created.cost_points == 300
        assert created.status == TicketStatus.PURCHASED
        assert created.ticket_number.startswith("B0-")


class TestTicketRepositoryUpdate:
    """TicketRepository.update() 메서드 테스트."""

    async def test_update_ticket_status_success(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_tickets: list[TicketModel],
    ):
        """티켓 상태를 업데이트할 수 있어야 합니다."""
        # Given: PURCHASED 상태인 첫 번째 티켓을 BOARDING으로 변경
        ticket_model = sample_tickets[0]
        ticket = await ticket_repository.find_by_id(Id(str(ticket_model.ticket_id)))
        assert ticket is not None
        assert ticket.status == TicketStatus.PURCHASED

        # When: 상태를 BOARDING으로 변경
        ticket.status = TicketStatus.BOARDING
        updated = await ticket_repository.update(ticket)

        # Then
        assert updated is not None
        assert updated.status == TicketStatus.BOARDING
        assert str(updated.ticket_id.value) == str(ticket_model.ticket_id)

    async def test_update_non_existent_ticket_raises_error(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_user: UserModel,
        sample_city: CityModel,
        sample_airship: AirshipModel,
    ):
        """존재하지 않는 티켓 업데이트 시 NotFoundTicketError 발생."""
        # Given: 존재하지 않는 티켓 엔티티
        now = datetime.now()
        city_snapshot = CitySnapshot(
            city_id=Id(str(sample_city.city_id)),
            name=sample_city.name,
            theme=sample_city.theme,
            image_url=sample_city.image_url,
            description=sample_city.description,
            base_cost_points=sample_city.base_cost_points,
            base_duration_minutes=sample_city.base_duration_minutes,
        )
        airship_snapshot = AirshipSnapshot(
            airship_id=Id(str(sample_airship.airship_id)),
            name=sample_airship.name,
            image_url=sample_airship.image_url,
            description=sample_airship.description,
            cost_factor=sample_airship.cost_factor,
            duration_factor=sample_airship.duration_factor,
        )

        non_existent_ticket = Ticket(
            ticket_id=Id(),  # 새로운 ID (DB에 없음)
            user_id=Id(str(sample_user.user_id)),
            city_snapshot=city_snapshot,
            airship_snapshot=airship_snapshot,
            ticket_number="B0-2025-NONEXIST",
            cost_points=300,
            status=TicketStatus.BOARDING,
            departure_datetime=now,
            arrival_datetime=now + timedelta(hours=24),
            created_at=now,
            updated_at=now,
        )

        # When/Then: NotFoundTicketError 발생
        with pytest.raises(NotFoundTicketError):
            await ticket_repository.update(non_existent_ticket)


class TestTicketRepositoryFindById:
    """TicketRepository.find_by_id() 메서드 테스트."""

    async def test_find_by_id_success(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_tickets: list[TicketModel],
    ):
        """ID로 티켓을 조회할 수 있어야 합니다."""
        # Given
        ticket_model = sample_tickets[0]

        # When
        ticket = await ticket_repository.find_by_id(Id(str(ticket_model.ticket_id)))

        # Then
        assert ticket is not None
        assert str(ticket.ticket_id.value) == str(ticket_model.ticket_id)
        assert ticket.ticket_number == ticket_model.ticket_number
        assert ticket.status == TicketStatus.PURCHASED

    async def test_find_by_id_returns_none_when_not_found(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
    ):
        """존재하지 않는 ID로 조회 시 None을 반환해야 합니다."""
        # Given: 존재하지 않는 ID
        non_existent_id = Id()

        # When
        ticket = await ticket_repository.find_by_id(non_existent_id)

        # Then
        assert ticket is None

    async def test_find_by_id_soft_deleted_excluded(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_tickets: list[TicketModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 티켓은 조회되지 않아야 합니다."""
        # Given: 티켓을 soft delete
        ticket_model = sample_tickets[0]
        ticket_model.deleted_at = datetime.now()
        await test_session.flush()

        # When
        ticket = await ticket_repository.find_by_id(Id(str(ticket_model.ticket_id)))

        # Then
        assert ticket is None


class TestTicketRepositoryFindAllByUserId:
    """TicketRepository.find_all_by_user_id() 메서드 테스트."""

    async def test_find_all_by_user_id_success(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_user: UserModel,
        sample_tickets: list[TicketModel],
    ):
        """사용자 ID로 티켓 목록을 조회할 수 있어야 합니다."""
        # When
        tickets = await ticket_repository.find_all_by_user_id(Id(str(sample_user.user_id)))

        # Then
        assert len(tickets) == 4
        assert all(str(t.user_id.value) == str(sample_user.user_id) for t in tickets)

    async def test_find_all_by_user_id_ordered_by_departure_desc(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_user: UserModel,
        sample_tickets: list[TicketModel],
    ):
        """티켓 목록은 departure_datetime 내림차순으로 정렬되어야 합니다."""
        # When
        tickets = await ticket_repository.find_all_by_user_id(Id(str(sample_user.user_id)))

        # Then
        assert len(tickets) == 4
        for i in range(len(tickets) - 1):
            assert tickets[i].departure_datetime >= tickets[i + 1].departure_datetime

    async def test_find_all_by_user_id_with_pagination(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_user: UserModel,
        sample_tickets: list[TicketModel],
    ):
        """pagination 파라미터로 티켓 목록을 조회할 수 있어야 합니다."""
        # When
        tickets = await ticket_repository.find_all_by_user_id(Id(str(sample_user.user_id)), offset=0, limit=2)

        # Then
        assert len(tickets) == 2

    async def test_find_all_by_user_id_with_offset(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_user: UserModel,
        sample_tickets: list[TicketModel],
    ):
        """offset 파라미터로 시작 위치를 지정할 수 있어야 합니다."""
        # When
        tickets = await ticket_repository.find_all_by_user_id(Id(str(sample_user.user_id)), offset=2, limit=10)

        # Then
        assert len(tickets) == 2

    async def test_find_all_by_user_id_soft_deleted_excluded(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_user: UserModel,
        sample_tickets: list[TicketModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 티켓은 조회되지 않아야 합니다."""
        # Given: 티켓 하나를 soft delete
        ticket_model = sample_tickets[0]
        ticket_model.deleted_at = datetime.now()
        await test_session.flush()

        # When
        tickets = await ticket_repository.find_all_by_user_id(Id(str(sample_user.user_id)))

        # Then: 3개만 조회됨
        assert len(tickets) == 3
        assert all(str(t.ticket_id.value) != str(ticket_model.ticket_id) for t in tickets)

    async def test_find_all_by_user_id_empty(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
    ):
        """티켓이 없으면 빈 리스트를 반환해야 합니다."""
        # Given: 존재하지 않는 사용자 ID
        non_existent_user_id = Id()

        # When
        tickets = await ticket_repository.find_all_by_user_id(non_existent_user_id)

        # Then
        assert tickets == []


class TestTicketRepositoryFindAllByUserIdAndStatus:
    """TicketRepository.find_all_by_user_id_and_status() 메서드 테스트."""

    async def test_find_all_by_user_id_and_status_purchased(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_user: UserModel,
        sample_tickets: list[TicketModel],
    ):
        """사용자 ID와 상태로 티켓을 조회할 수 있어야 합니다."""
        # When
        tickets = await ticket_repository.find_all_by_user_id_and_status(
            Id(str(sample_user.user_id)), TicketStatus.PURCHASED
        )

        # Then
        assert len(tickets) == 1
        assert tickets[0].status == TicketStatus.PURCHASED

    async def test_find_all_by_user_id_and_status_filters_other_statuses(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_user: UserModel,
        sample_tickets: list[TicketModel],
    ):
        """다른 상태의 티켓은 필터링되어야 합니다."""
        # When: BOARDING 상태 티켓만 조회
        tickets = await ticket_repository.find_all_by_user_id_and_status(
            Id(str(sample_user.user_id)), TicketStatus.BOARDING
        )

        # Then
        assert len(tickets) == 1
        assert all(t.status == TicketStatus.BOARDING for t in tickets)

    async def test_find_all_by_user_id_and_status_ordered_by_departure_desc(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_user: UserModel,
        sample_tickets: list[TicketModel],
        test_session: AsyncSession,
    ):
        """티켓 목록은 departure_datetime 내림차순으로 정렬되어야 합니다."""
        # Given: PURCHASED 상태 티켓 추가 생성
        now = datetime.now()
        ticket_model = TicketModel(
            ticket_id=uuid7(),
            user_id=sample_user.user_id,
            city_id=sample_tickets[0].city_id,
            city_name=sample_tickets[0].city_name,
            city_theme=sample_tickets[0].city_theme,
            city_description=sample_tickets[0].city_description,
            city_image_url=sample_tickets[0].city_image_url,
            city_base_cost_points=sample_tickets[0].city_base_cost_points,
            city_base_duration_minutes=sample_tickets[0].city_base_duration_minutes,
            airship_id=sample_tickets[0].airship_id,
            airship_name=sample_tickets[0].airship_name,
            airship_description=sample_tickets[0].airship_description,
            airship_image_url=sample_tickets[0].airship_image_url,
            airship_cost_factor=sample_tickets[0].airship_cost_factor,
            airship_duration_factor=sample_tickets[0].airship_duration_factor,
            ticket_number="B0-2025-TEST005",
            cost_points=300,
            status=TicketStatus.PURCHASED.value,
            departure_datetime=now + timedelta(hours=3),
            arrival_datetime=now + timedelta(hours=27),
            created_at=now,
            updated_at=now,
        )
        test_session.add(ticket_model)
        await test_session.flush()

        # When
        tickets = await ticket_repository.find_all_by_user_id_and_status(
            Id(str(sample_user.user_id)), TicketStatus.PURCHASED
        )

        # Then
        assert len(tickets) == 2
        assert tickets[0].departure_datetime >= tickets[1].departure_datetime

    async def test_find_all_by_user_id_and_status_soft_deleted_excluded(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_user: UserModel,
        sample_tickets: list[TicketModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 티켓은 조회되지 않아야 합니다."""
        # Given: PURCHASED 상태 티켓을 soft delete
        ticket_model = sample_tickets[0]
        assert ticket_model.status == TicketStatus.PURCHASED.value
        ticket_model.deleted_at = datetime.now()
        await test_session.flush()

        # When
        tickets = await ticket_repository.find_all_by_user_id_and_status(
            Id(str(sample_user.user_id)), TicketStatus.PURCHASED
        )

        # Then
        assert len(tickets) == 0

    async def test_find_all_by_user_id_and_status_with_pagination(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_user: UserModel,
        sample_tickets: list[TicketModel],
        test_session: AsyncSession,
    ):
        """pagination 파라미터로 티켓 목록을 조회할 수 있어야 합니다."""
        # Given: PURCHASED 상태 티켓 추가 생성
        now = datetime.now()
        ticket_model = TicketModel(
            ticket_id=uuid7(),
            user_id=sample_user.user_id,
            city_id=sample_tickets[0].city_id,
            city_name=sample_tickets[0].city_name,
            city_theme=sample_tickets[0].city_theme,
            city_description=sample_tickets[0].city_description,
            city_image_url=sample_tickets[0].city_image_url,
            city_base_cost_points=sample_tickets[0].city_base_cost_points,
            city_base_duration_minutes=sample_tickets[0].city_base_duration_minutes,
            airship_id=sample_tickets[0].airship_id,
            airship_name=sample_tickets[0].airship_name,
            airship_description=sample_tickets[0].airship_description,
            airship_image_url=sample_tickets[0].airship_image_url,
            airship_cost_factor=sample_tickets[0].airship_cost_factor,
            airship_duration_factor=sample_tickets[0].airship_duration_factor,
            ticket_number="B0-2025-TEST005",
            cost_points=300,
            status=TicketStatus.PURCHASED.value,
            departure_datetime=now + timedelta(hours=3),
            arrival_datetime=now + timedelta(hours=27),
            created_at=now,
            updated_at=now,
        )
        test_session.add(ticket_model)
        await test_session.flush()

        # When
        tickets = await ticket_repository.find_all_by_user_id_and_status(
            Id(str(sample_user.user_id)), TicketStatus.PURCHASED, offset=0, limit=1
        )

        # Then
        assert len(tickets) == 1


class TestTicketRepositoryCountBy:
    """TicketRepository.count_by() 메서드 테스트."""

    async def test_count_by_user_id_only(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_user: UserModel,
        sample_tickets: list[TicketModel],
    ):
        """user_id로 티켓 개수를 조회할 수 있어야 합니다."""
        # When
        count = await ticket_repository.count_by(user_id=Id(str(sample_user.user_id)))

        # Then
        assert count == 4

    async def test_count_by_user_id_and_status(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_user: UserModel,
        sample_tickets: list[TicketModel],
    ):
        """user_id와 status로 티켓 개수를 조회할 수 있어야 합니다."""
        # When
        count = await ticket_repository.count_by(user_id=Id(str(sample_user.user_id)), status=TicketStatus.PURCHASED)

        # Then
        assert count == 1

    async def test_count_by_status_only(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_tickets: list[TicketModel],
    ):
        """status로만 티켓 개수를 조회할 수 있어야 합니다."""
        # When
        count = await ticket_repository.count_by(status=TicketStatus.BOARDING)

        # Then
        assert count == 1

    async def test_count_by_no_filters(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_tickets: list[TicketModel],
    ):
        """필터 없이 전체 티켓 개수를 조회할 수 있어야 합니다."""
        # When
        count = await ticket_repository.count_by()

        # Then
        assert count == 4

    async def test_count_by_soft_deleted_excluded(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        sample_user: UserModel,
        sample_tickets: list[TicketModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 티켓은 카운트에서 제외되어야 합니다."""
        # Given: 티켓 하나를 soft delete
        ticket_model = sample_tickets[0]
        ticket_model.deleted_at = datetime.now()
        await test_session.flush()

        # When
        count = await ticket_repository.count_by(user_id=Id(str(sample_user.user_id)))

        # Then: 3개만 카운트됨
        assert count == 3

    async def test_count_by_returns_zero_when_no_results(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
    ):
        """조건에 맞는 티켓이 없으면 0을 반환해야 합니다."""
        # Given: 존재하지 않는 사용자 ID
        non_existent_user_id = Id()

        # When
        count = await ticket_repository.count_by(user_id=non_existent_user_id)

        # Then
        assert count == 0
