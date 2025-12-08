"""TicketService Integration Tests."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.domain.entities import Airship, City, Ticket, User
from bzero.domain.errors import (
    ForbiddenTicketError,
    InsufficientBalanceError,
    InvalidAirshipStatusError,
    InvalidCityStatusError,
    NotFoundTicketError,
)
from bzero.domain.services.ticket import TicketService
from bzero.domain.value_objects import Balance, Email, Id, Nickname, Profile, TicketStatus
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.ticket import SqlAlchemyTicketRepository


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone"""
    return ZoneInfo("Asia/Seoul")


@pytest.fixture
def ticket_service(test_session: AsyncSession, timezone: ZoneInfo) -> TicketService:
    """TicketService fixture를 생성합니다."""
    ticket_repository = SqlAlchemyTicketRepository(test_session)
    return TicketService(ticket_repository, timezone)


@pytest.fixture
async def sample_user(test_session: AsyncSession) -> User:
    """테스트용 샘플 유저 데이터를 생성합니다."""
    now = datetime.now()
    user_model = UserModel(
        user_id=uuid7(),
        email="test@example.com",
        nickname="테스트유저",
        profile_emoji="🌟",
        current_points=1000,
        created_at=now,
        updated_at=now,
    )
    test_session.add(user_model)
    await test_session.flush()

    return User(
        user_id=Id(user_model.user_id),
        email=Email(user_model.email),
        nickname=Nickname(user_model.nickname),
        profile=Profile(user_model.profile_emoji),
        current_points=Balance(user_model.current_points),
        created_at=user_model.created_at,
        updated_at=user_model.updated_at,
    )


@pytest.fixture
async def sample_user_with_insufficient_balance(test_session: AsyncSession) -> User:
    """잔액이 부족한 테스트용 샘플 유저 데이터를 생성합니다."""
    now = datetime.now()
    user_model = UserModel(
        user_id=uuid7(),
        email="poor@example.com",
        nickname="가난한유저",
        profile_emoji="🤔",
        current_points=100,  # 잔액 부족
        created_at=now,
        updated_at=now,
    )
    test_session.add(user_model)
    await test_session.flush()

    return User(
        user_id=Id(user_model.user_id),
        email=Email(user_model.email),
        nickname=Nickname(user_model.nickname),
        profile=Profile(user_model.profile_emoji),
        current_points=Balance(user_model.current_points),
        created_at=user_model.created_at,
        updated_at=user_model.updated_at,
    )


@pytest.fixture
async def sample_city(test_session: AsyncSession) -> City:
    """테스트용 샘플 도시 데이터를 생성합니다."""
    now = datetime.now()
    city_model = CityModel(
        city_id=uuid7(),
        name="세렌시아",
        theme="관계",
        image_url="https://example.com/serencia.jpg",
        description="노을빛 항구 마을",
        base_cost_points=300,
        base_duration_hours=24,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(city_model)
    await test_session.flush()

    return City(
        city_id=Id(city_model.city_id),
        name=city_model.name,
        theme=city_model.theme,
        image_url=city_model.image_url,
        description=city_model.description,
        base_cost_points=city_model.base_cost_points,
        base_duration_hours=city_model.base_duration_hours,
        display_order=city_model.display_order,
        is_active=city_model.is_active,
        created_at=city_model.created_at,
        updated_at=city_model.updated_at,
    )


@pytest.fixture
async def sample_inactive_city(test_session: AsyncSession) -> City:
    """비활성화된 테스트용 샘플 도시 데이터를 생성합니다."""
    now = datetime.now()
    city_model = CityModel(
        city_id=uuid7(),
        name="비활성도시",
        theme="테스트",
        image_url=None,
        description="비활성화된 도시",
        base_cost_points=300,
        base_duration_hours=24,
        display_order=10,
        is_active=False,  # 비활성
        created_at=now,
        updated_at=now,
    )
    test_session.add(city_model)
    await test_session.flush()

    return City(
        city_id=Id(city_model.city_id),
        name=city_model.name,
        theme=city_model.theme,
        image_url=city_model.image_url,
        description=city_model.description,
        base_cost_points=city_model.base_cost_points,
        base_duration_hours=city_model.base_duration_hours,
        display_order=city_model.display_order,
        is_active=city_model.is_active,
        created_at=city_model.created_at,
        updated_at=city_model.updated_at,
    )


@pytest.fixture
async def sample_airship(test_session: AsyncSession) -> Airship:
    """테스트용 샘플 비행선 데이터를 생성합니다."""
    now = datetime.now()
    airship_model = AirshipModel(
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
    test_session.add(airship_model)
    await test_session.flush()

    return Airship(
        airship_id=Id(airship_model.airship_id),
        name=airship_model.name,
        description=airship_model.description,
        image_url=airship_model.image_url,
        cost_factor=airship_model.cost_factor,
        duration_factor=airship_model.duration_factor,
        display_order=airship_model.display_order,
        is_active=airship_model.is_active,
        created_at=airship_model.created_at,
        updated_at=airship_model.updated_at,
    )


@pytest.fixture
async def sample_inactive_airship(test_session: AsyncSession) -> Airship:
    """비활성화된 테스트용 샘플 비행선 데이터를 생성합니다."""
    now = datetime.now()
    airship_model = AirshipModel(
        airship_id=uuid7(),
        name="비활성 비행선",
        description="비활성화된 비행선",
        image_url=None,
        cost_factor=1,
        duration_factor=1,
        display_order=10,
        is_active=False,  # 비활성
        created_at=now,
        updated_at=now,
    )
    test_session.add(airship_model)
    await test_session.flush()

    return Airship(
        airship_id=Id(airship_model.airship_id),
        name=airship_model.name,
        description=airship_model.description,
        image_url=airship_model.image_url,
        cost_factor=airship_model.cost_factor,
        duration_factor=airship_model.duration_factor,
        display_order=airship_model.display_order,
        is_active=airship_model.is_active,
        created_at=airship_model.created_at,
        updated_at=airship_model.updated_at,
    )


@pytest.fixture
async def sample_ticket(
    test_session: AsyncSession, sample_user: User, sample_city: City, sample_airship: Airship, timezone: ZoneInfo
) -> Ticket:
    """테스트용 샘플 티켓 데이터를 생성합니다."""
    now = datetime.now(timezone)
    ticket = Ticket.create(
        user_id=sample_user.user_id,
        city_snapshot=sample_city.snapshot(),
        airship_snapshot=sample_airship.snapshot(),
        cost_points=300,
        departure_datetime=now,
        arrival_datetime=now + timedelta(hours=24),
        created_at=now,
        updated_at=now,
    )

    ticket_model = TicketModel(
        ticket_id=ticket.ticket_id.value,
        user_id=ticket.user_id.value,
        ticket_number=ticket.ticket_number,
        cost_points=ticket.cost_points,
        status=ticket.status.value,
        departure_datetime=ticket.departure_datetime,
        arrival_datetime=ticket.arrival_datetime,
        city_id=ticket.city_snapshot.city_id.value,
        city_name=ticket.city_snapshot.name,
        city_theme=ticket.city_snapshot.theme,
        city_image_url=ticket.city_snapshot.image_url,
        city_description=ticket.city_snapshot.description,
        city_base_cost_points=ticket.city_snapshot.base_cost_points,
        city_base_duration_hours=ticket.city_snapshot.base_duration_hours,
        airship_id=ticket.airship_snapshot.airship_id.value,
        airship_name=ticket.airship_snapshot.name,
        airship_image_url=ticket.airship_snapshot.image_url,
        airship_description=ticket.airship_snapshot.description,
        airship_cost_factor=ticket.airship_snapshot.cost_factor,
        airship_duration_factor=ticket.airship_snapshot.duration_factor,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )

    test_session.add(ticket_model)
    await test_session.flush()

    return ticket


class TestTicketServicePurchaseTicket:
    """purchase_ticket 메서드 통합 테스트"""

    async def test_purchase_ticket_success(
        self,
        ticket_service: TicketService,
        sample_user: User,
        sample_city: City,
        sample_airship: Airship,
        test_session: AsyncSession,
    ):
        """티켓을 성공적으로 구매할 수 있어야 합니다."""
        # When
        ticket = await ticket_service.purchase_ticket(sample_user, sample_city, sample_airship)

        # Then
        assert ticket.ticket_id is not None
        assert str(ticket.user_id.value) == str(sample_user.user_id.value)
        assert str(ticket.city_snapshot.city_id.value) == str(sample_city.city_id.value)
        assert str(ticket.airship_snapshot.airship_id.value) == str(sample_airship.airship_id.value)
        assert ticket.cost_points == 300  # 300 x 1
        assert ticket.status == TicketStatus.BOARDING  # consume()가 호출되어 BOARDING

        # DB에 저장되었는지 확인
        stmt = select(TicketModel).where(TicketModel.ticket_id == ticket.ticket_id.value)
        result = await test_session.execute(stmt)
        saved_model = result.scalar_one_or_none()
        assert saved_model is not None
        assert saved_model.status == TicketStatus.BOARDING.value

    async def test_purchase_ticket_calculates_cost_correctly(
        self, ticket_service: TicketService, sample_user: User, sample_city: City, test_session: AsyncSession
    ):
        """티켓 비용이 올바르게 계산되어야 합니다."""
        # Given: 쾌속 비행선 (비용 배율 2배)
        now = datetime.now()
        fast_airship_model = AirshipModel(
            airship_id=uuid7(),
            name="쾌속 비행선",
            description="빠른 이동",
            image_url=None,
            cost_factor=2,
            duration_factor=1,
            display_order=2,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        test_session.add(fast_airship_model)
        await test_session.flush()

        fast_airship = Airship(
            airship_id=Id(fast_airship_model.airship_id),
            name=fast_airship_model.name,
            description=fast_airship_model.description,
            image_url=fast_airship_model.image_url,
            cost_factor=fast_airship_model.cost_factor,
            duration_factor=fast_airship_model.duration_factor,
            display_order=fast_airship_model.display_order,
            is_active=fast_airship_model.is_active,
            created_at=fast_airship_model.created_at,
            updated_at=fast_airship_model.updated_at,
        )

        # When
        ticket = await ticket_service.purchase_ticket(sample_user, sample_city, fast_airship)

        # Then: 300 x 2 = 600
        assert ticket.cost_points == 600

    async def test_purchase_ticket_raises_error_when_insufficient_balance(
        self,
        ticket_service: TicketService,
        sample_user_with_insufficient_balance: User,
        sample_city: City,
        sample_airship: Airship,
    ):
        """잔액이 부족하면 에러가 발생해야 합니다."""
        # Given: 유저 잔액 100, 티켓 비용 300
        assert sample_user_with_insufficient_balance.current_points.value == 100

        # When/Then
        with pytest.raises(InsufficientBalanceError):
            await ticket_service.purchase_ticket(sample_user_with_insufficient_balance, sample_city, sample_airship)

    async def test_purchase_ticket_raises_error_when_city_is_inactive(
        self,
        ticket_service: TicketService,
        sample_user: User,
        sample_inactive_city: City,
        sample_airship: Airship,
    ):
        """도시가 비활성화되어 있으면 에러가 발생해야 합니다."""
        # When/Then
        with pytest.raises(InvalidCityStatusError):
            await ticket_service.purchase_ticket(sample_user, sample_inactive_city, sample_airship)

    async def test_purchase_ticket_raises_error_when_airship_is_inactive(
        self,
        ticket_service: TicketService,
        sample_user: User,
        sample_city: City,
        sample_inactive_airship: Airship,
    ):
        """비행선이 비활성화되어 있으면 에러가 발생해야 합니다."""
        # When/Then
        with pytest.raises(InvalidAirshipStatusError):
            await ticket_service.purchase_ticket(sample_user, sample_city, sample_inactive_airship)


class TestTicketServiceComplete:
    """complete 메서드 통합 테스트"""

    async def test_complete_ticket_success(
        self,
        ticket_service: TicketService,
        sample_ticket: Ticket,
        test_session: AsyncSession,
    ):
        """티켓을 성공적으로 완료할 수 있어야 합니다."""
        # Given: BOARDING 상태의 티켓
        stmt = (
            update(TicketModel)
            .where(TicketModel.ticket_id == sample_ticket.ticket_id.value)
            .values(status=TicketStatus.BOARDING.value)
        )
        await test_session.execute(stmt)
        await test_session.flush()

        # When: DB에서 조회한 티켓의 user_id를 사용 (UUID 타입 호환성 문제 해결)
        ticket_from_db = await ticket_service.get_ticket_by_id(sample_ticket.ticket_id)
        completed_ticket = await ticket_service.complete(ticket_from_db.user_id, sample_ticket.ticket_id)

        # Then
        assert completed_ticket.status == TicketStatus.COMPLETED

        # DB에 업데이트되었는지 확인
        stmt = select(TicketModel).where(TicketModel.ticket_id == sample_ticket.ticket_id.value)
        result = await test_session.execute(stmt)
        saved_model = result.scalar_one_or_none()
        assert saved_model is not None
        assert saved_model.status == TicketStatus.COMPLETED.value

    async def test_complete_raises_error_when_ticket_not_found(
        self,
        ticket_service: TicketService,
        sample_user: User,
    ):
        """티켓을 찾을 수 없으면 에러가 발생해야 합니다."""
        # Given
        non_existent_ticket_id = Id(uuid7())

        # When/Then
        with pytest.raises(NotFoundTicketError):
            await ticket_service.complete(sample_user.user_id, non_existent_ticket_id)

    async def test_complete_raises_error_when_forbidden_user(
        self,
        ticket_service: TicketService,
        sample_ticket: Ticket,
        test_session: AsyncSession,
    ):
        """다른 사용자의 티켓을 완료하려 하면 에러가 발생해야 합니다."""
        # Given: BOARDING 상태로 변경
        sample_ticket.consume()
        stmt = (
            update(TicketModel)
            .where(TicketModel.ticket_id == sample_ticket.ticket_id.value)
            .values(status=TicketStatus.BOARDING.value)
        )
        await test_session.execute(stmt)
        await test_session.flush()

        # Given: 다른 사용자
        another_user_id = Id(uuid7())

        # When/Then
        with pytest.raises(ForbiddenTicketError):
            await ticket_service.complete(another_user_id, sample_ticket.ticket_id)


class TestTicketServiceCancel:
    """cancel 메서드 통합 테스트"""

    async def test_cancel_ticket_success(
        self,
        ticket_service: TicketService,
        sample_ticket: Ticket,
        test_session: AsyncSession,
    ):
        """티켓을 성공적으로 취소할 수 있어야 합니다."""
        # Given: PURCHASED 상태의 티켓
        assert sample_ticket.status == TicketStatus.PURCHASED

        # When: DB에서 조회한 티켓의 user_id를 사용 (UUID 타입 호환성 문제 해결)
        ticket_from_db = await ticket_service.get_ticket_by_id(sample_ticket.ticket_id)
        cancelled_ticket = await ticket_service.cancel(ticket_from_db.user_id, sample_ticket.ticket_id)

        # Then
        assert cancelled_ticket.status == TicketStatus.CANCELLED

        # DB에 업데이트되었는지 확인
        stmt = select(TicketModel).where(TicketModel.ticket_id == sample_ticket.ticket_id.value)
        result = await test_session.execute(stmt)
        saved_model = result.scalar_one_or_none()
        assert saved_model is not None
        assert saved_model.status == TicketStatus.CANCELLED.value

    async def test_cancel_raises_error_when_ticket_not_found(
        self,
        ticket_service: TicketService,
        sample_user: User,
    ):
        """티켓을 찾을 수 없으면 에러가 발생해야 합니다."""
        # Given
        non_existent_ticket_id = Id(uuid7())

        # When/Then
        with pytest.raises(NotFoundTicketError):
            await ticket_service.cancel(sample_user.user_id, non_existent_ticket_id)

    async def test_cancel_raises_error_when_forbidden_user(
        self,
        ticket_service: TicketService,
        sample_ticket: Ticket,
    ):
        """다른 사용자의 티켓을 취소하려 하면 에러가 발생해야 합니다."""
        # Given: 다른 사용자
        another_user_id = Id(uuid7())

        # When/Then
        with pytest.raises(ForbiddenTicketError):
            await ticket_service.cancel(another_user_id, sample_ticket.ticket_id)


class TestTicketServiceGetTicketById:
    """get_ticket_by_id 메서드 통합 테스트"""

    async def test_get_ticket_by_id_success(
        self,
        ticket_service: TicketService,
        sample_ticket: Ticket,
    ):
        """티켓을 ID로 조회할 수 있어야 합니다."""
        # When
        ticket = await ticket_service.get_ticket_by_id(sample_ticket.ticket_id)

        # Then
        assert str(ticket.ticket_id.value) == str(sample_ticket.ticket_id.value)
        assert str(ticket.user_id.value) == str(sample_ticket.user_id.value)
        assert str(ticket.city_snapshot.city_id.value) == str(sample_ticket.city_snapshot.city_id.value)

    async def test_get_ticket_by_id_raises_error_when_not_found(
        self,
        ticket_service: TicketService,
    ):
        """티켓을 찾을 수 없으면 에러가 발생해야 합니다."""
        # Given
        non_existent_ticket_id = Id(uuid7())

        # When/Then
        with pytest.raises(NotFoundTicketError):
            await ticket_service.get_ticket_by_id(non_existent_ticket_id)

    async def test_get_ticket_by_id_with_user_id_success(
        self,
        ticket_service: TicketService,
        sample_ticket: Ticket,
    ):
        """사용자 ID를 포함하여 티켓을 조회할 수 있어야 합니다."""
        # Given: DB에서 조회한 티켓의 user_id를 사용 (UUID 타입 호환성 문제 해결)
        ticket_from_db = await ticket_service.get_ticket_by_id(sample_ticket.ticket_id)

        # When
        ticket = await ticket_service.get_ticket_by_id(sample_ticket.ticket_id, ticket_from_db.user_id)

        # Then
        assert str(ticket.ticket_id.value) == str(sample_ticket.ticket_id.value)
        assert str(ticket.user_id.value) == str(ticket_from_db.user_id.value)

    async def test_get_ticket_by_id_raises_error_when_forbidden_user(
        self,
        ticket_service: TicketService,
        sample_ticket: Ticket,
    ):
        """다른 사용자의 티켓을 조회하려 하면 에러가 발생해야 합니다."""
        # Given
        another_user_id = Id(uuid7())

        # When/Then
        with pytest.raises(ForbiddenTicketError):
            await ticket_service.get_ticket_by_id(sample_ticket.ticket_id, another_user_id)


class TestTicketServiceGetAllTicketsByUserId:
    """get_all_tickets_by_user_id 메서드 통합 테스트"""

    async def test_get_all_tickets_by_user_id_success(
        self,
        ticket_service: TicketService,
        sample_ticket: Ticket,
    ):
        """사용자의 모든 티켓을 조회할 수 있어야 합니다."""
        # When: sample_ticket의 user_id를 사용
        tickets, total = await ticket_service.get_all_tickets_by_user_id(sample_ticket.user_id)

        # Then
        assert len(tickets) == 1
        assert total == 1
        assert str(tickets[0].user_id.value) == str(sample_ticket.user_id.value)

    async def test_get_all_tickets_by_user_id_with_pagination(
        self,
        ticket_service: TicketService,
        sample_user: User,
        sample_city: City,
        sample_airship: Airship,
        test_session: AsyncSession,
        timezone: ZoneInfo,
    ):
        """pagination 파라미터로 티켓 목록을 조회할 수 있어야 합니다."""
        # Given: 4개의 티켓 생성 (pagination 테스트용)
        now = datetime.now(timezone)
        for i in range(4):
            departure = now + timedelta(hours=i)
            ticket = Ticket.create(
                user_id=sample_user.user_id,
                city_snapshot=sample_city.snapshot(),
                airship_snapshot=sample_airship.snapshot(),
                cost_points=300,
                departure_datetime=departure,
                arrival_datetime=departure + timedelta(hours=24),
                created_at=departure,
                updated_at=departure,
            )
            ticket_model = TicketModel(
                ticket_id=ticket.ticket_id.value,
                user_id=ticket.user_id.value,
                ticket_number=ticket.ticket_number,
                cost_points=ticket.cost_points,
                status=ticket.status.value,
                departure_datetime=ticket.departure_datetime,
                arrival_datetime=ticket.arrival_datetime,
                city_id=ticket.city_snapshot.city_id.value,
                city_name=ticket.city_snapshot.name,
                city_theme=ticket.city_snapshot.theme,
                city_image_url=ticket.city_snapshot.image_url,
                city_description=ticket.city_snapshot.description,
                city_base_cost_points=ticket.city_snapshot.base_cost_points,
                city_base_duration_hours=ticket.city_snapshot.base_duration_hours,
                airship_id=ticket.airship_snapshot.airship_id.value,
                airship_name=ticket.airship_snapshot.name,
                airship_image_url=ticket.airship_snapshot.image_url,
                airship_description=ticket.airship_snapshot.description,
                airship_cost_factor=ticket.airship_snapshot.cost_factor,
                airship_duration_factor=ticket.airship_snapshot.duration_factor,
                created_at=ticket.created_at,
                updated_at=ticket.updated_at,
            )
            test_session.add(ticket_model)
        await test_session.flush()

        # When: 첫 번째 페이지 (2개)
        tickets, total = await ticket_service.get_all_tickets_by_user_id(sample_user.user_id, offset=0, limit=2)

        # Then
        assert len(tickets) == 2
        assert total == 4  # 4개 생성됨

    async def test_get_all_tickets_by_user_id_returns_empty_list(
        self,
        ticket_service: TicketService,
    ):
        """티켓이 없으면 빈 리스트를 반환해야 합니다."""
        # Given
        user_id = Id(uuid7())

        # When
        tickets, total = await ticket_service.get_all_tickets_by_user_id(user_id)

        # Then
        assert tickets == []
        assert total == 0


class TestTicketServiceGetAllTicketsByUserIdAndStatus:
    """get_all_tickets_by_user_id_and_status 메서드 통합 테스트"""

    async def test_get_all_tickets_by_user_id_and_status_success(
        self,
        ticket_service: TicketService,
        sample_ticket: Ticket,
    ):
        """사용자의 특정 상태 티켓을 조회할 수 있어야 합니다."""
        # When: sample_ticket의 user_id를 사용
        tickets, total = await ticket_service.get_all_tickets_by_user_id_and_status(
            sample_ticket.user_id, TicketStatus.PURCHASED
        )

        # Then
        assert len(tickets) == 1
        assert total == 1
        assert tickets[0].status == TicketStatus.PURCHASED

    async def test_get_all_tickets_by_user_id_and_status_with_multiple_tickets(
        self,
        ticket_service: TicketService,
        sample_user: User,
        sample_city: City,
        sample_airship: Airship,
        test_session: AsyncSession,
        timezone: ZoneInfo,
    ):
        """다양한 상태의 티켓 중 특정 상태만 조회할 수 있어야 합니다."""
        # Given: PURCHASED 2개, BOARDING 1개, COMPLETED 1개
        now = datetime.now(timezone)
        statuses = [
            TicketStatus.PURCHASED,
            TicketStatus.PURCHASED,
            TicketStatus.BOARDING,
            TicketStatus.COMPLETED,
        ]

        for i, status in enumerate(statuses):
            departure = now + timedelta(hours=i)
            ticket = Ticket.create(
                user_id=sample_user.user_id,
                city_snapshot=sample_city.snapshot(),
                airship_snapshot=sample_airship.snapshot(),
                cost_points=300,
                departure_datetime=departure,
                arrival_datetime=departure + timedelta(hours=24),
                created_at=departure,
                updated_at=departure,
            )
            ticket_model = TicketModel(
                ticket_id=ticket.ticket_id.value,
                user_id=ticket.user_id.value,
                ticket_number=ticket.ticket_number,
                cost_points=ticket.cost_points,
                status=status.value,
                departure_datetime=ticket.departure_datetime,
                arrival_datetime=ticket.arrival_datetime,
                city_id=ticket.city_snapshot.city_id.value,
                city_name=ticket.city_snapshot.name,
                city_theme=ticket.city_snapshot.theme,
                city_image_url=ticket.city_snapshot.image_url,
                city_description=ticket.city_snapshot.description,
                city_base_cost_points=ticket.city_snapshot.base_cost_points,
                city_base_duration_hours=ticket.city_snapshot.base_duration_hours,
                airship_id=ticket.airship_snapshot.airship_id.value,
                airship_name=ticket.airship_snapshot.name,
                airship_image_url=ticket.airship_snapshot.image_url,
                airship_description=ticket.airship_snapshot.description,
                airship_cost_factor=ticket.airship_snapshot.cost_factor,
                airship_duration_factor=ticket.airship_snapshot.duration_factor,
                created_at=ticket.created_at,
                updated_at=ticket.updated_at,
            )
            test_session.add(ticket_model)
        await test_session.flush()

        # When: BOARDING 상태만 조회
        tickets, total = await ticket_service.get_all_tickets_by_user_id_and_status(
            sample_user.user_id, TicketStatus.BOARDING
        )

        # Then
        assert len(tickets) == 1
        assert total == 1
        assert all(t.status == TicketStatus.BOARDING for t in tickets)

    async def test_get_all_tickets_by_user_id_and_status_returns_empty_list(
        self,
        ticket_service: TicketService,
        sample_user: User,
    ):
        """해당 상태의 티켓이 없으면 빈 리스트를 반환해야 합니다."""
        # When: CANCELLED 상태 조회 (존재하지 않음)
        tickets, total = await ticket_service.get_all_tickets_by_user_id_and_status(
            sample_user.user_id, TicketStatus.CANCELLED
        )

        # Then
        assert tickets == []
        assert total == 0
