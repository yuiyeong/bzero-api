"""TicketService 단위 테스트"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest
from uuid_utils import uuid7

from bzero.domain.entities import Airship, City, Ticket, User
from bzero.domain.errors import (
    ForbiddenTicketError,
    InsufficientBalanceError,
    InvalidAirshipStatusError,
    InvalidCityStatusError,
    NotFoundTicketError,
)
from bzero.domain.repositories.ticket import TicketRepository
from bzero.domain.services.ticket import TicketService
from bzero.domain.value_objects import (
    Balance,
    Email,
    Id,
    Nickname,
    Profile,
    TicketStatus,
)


@pytest.fixture
def mock_ticket_repository() -> MagicMock:
    """Mock TicketRepository"""
    return MagicMock(spec=TicketRepository)


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone"""
    return ZoneInfo("Asia/Seoul")


@pytest.fixture
def ticket_service(mock_ticket_repository: MagicMock, timezone: ZoneInfo) -> TicketService:
    """TicketService with mocked repository"""
    return TicketService(mock_ticket_repository, timezone)


@pytest.fixture
def sample_user() -> User:
    """샘플 유저"""
    now = datetime.now()
    return User(
        user_id=Id(uuid7()),
        email=Email("test@example.com"),
        nickname=Nickname("테스트유저"),
        profile=Profile("🌟"),
        current_points=Balance(1000),
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_user_with_insufficient_balance() -> User:
    """잔액이 부족한 샘플 유저"""
    now = datetime.now()
    return User(
        user_id=Id(uuid7()),
        email=Email("poor@example.com"),
        nickname=Nickname("가난한유저"),
        profile=Profile("🤔"),
        current_points=Balance(100),
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_city() -> City:
    """샘플 도시"""
    now = datetime.now()
    return City(
        city_id=Id(uuid7()),
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


@pytest.fixture
def sample_inactive_city() -> City:
    """비활성화된 샘플 도시"""
    now = datetime.now()
    return City(
        city_id=Id(uuid7()),
        name="비활성도시",
        theme="테스트",
        image_url=None,
        description="비활성화된 도시",
        base_cost_points=300,
        base_duration_hours=24,
        display_order=10,
        is_active=False,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_airship() -> Airship:
    """샘플 비행선"""
    now = datetime.now()
    return Airship(
        airship_id=Id(uuid7()),
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


@pytest.fixture
def sample_inactive_airship() -> Airship:
    """비활성화된 샘플 비행선"""
    now = datetime.now()
    return Airship(
        airship_id=Id(uuid7()),
        name="비활성 비행선",
        description="비활성화된 비행선",
        image_url=None,
        cost_factor=1,
        duration_factor=1,
        display_order=10,
        is_active=False,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_ticket(sample_user: User, sample_city: City, sample_airship: Airship, timezone: ZoneInfo) -> Ticket:
    """샘플 티켓"""
    now = datetime.now(timezone)
    return Ticket.create(
        user_id=sample_user.user_id,
        city_snapshot=sample_city.snapshot(),
        airship_snapshot=sample_airship.snapshot(),
        cost_points=300,
        departure_datetime=now,
        arrival_datetime=now + timedelta(hours=24),
        created_at=now,
        updated_at=now,
    )


class TestTicketServicePurchaseTicket:
    """purchase_ticket 메서드 테스트"""

    async def test_purchase_ticket_success(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_user: User,
        sample_city: City,
        sample_airship: Airship,
    ):
        """티켓을 성공적으로 구매할 수 있다"""
        # Given
        expected_cost = sample_city.base_cost_points * sample_airship.cost_factor

        async def mock_create(ticket: Ticket) -> Ticket:
            return ticket

        mock_ticket_repository.create = AsyncMock(side_effect=mock_create)

        # When
        ticket = await ticket_service.purchase_ticket(sample_user, sample_city, sample_airship)

        # Then
        assert ticket.user_id == sample_user.user_id
        assert ticket.city_snapshot.city_id == sample_city.city_id
        assert ticket.airship_snapshot.airship_id == sample_airship.airship_id
        assert ticket.cost_points == expected_cost
        assert ticket.status == TicketStatus.BOARDING  # consume()가 호출되어 BOARDING 상태
        mock_ticket_repository.create.assert_called_once()

    async def test_purchase_ticket_raises_error_when_insufficient_balance(
        self,
        ticket_service: TicketService,
        sample_user_with_insufficient_balance: User,
        sample_city: City,
        sample_airship: Airship,
    ):
        """잔액이 부족하면 에러가 발생한다"""
        # Given: 유저 잔액 100, 티켓 비용 300
        assert sample_user_with_insufficient_balance.current_points.value == 100
        assert sample_city.base_cost_points * sample_airship.cost_factor == 300

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
        """도시가 비활성화되어 있으면 에러가 발생한다"""
        # Given
        assert sample_inactive_city.is_active is False

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
        """비행선이 비활성화되어 있으면 에러가 발생한다"""
        # Given
        assert sample_inactive_airship.is_active is False

        # When/Then
        with pytest.raises(InvalidAirshipStatusError):
            await ticket_service.purchase_ticket(sample_user, sample_city, sample_inactive_airship)

    async def test_purchase_ticket_calculates_cost_correctly(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_user: User,
        sample_city: City,
    ):
        """티켓 비용이 올바르게 계산된다 (도시 기본 비용 x 비행선 비용 배율)"""
        # Given: 쾌속 비행선 (비용 배율 2배)
        now = datetime.now()
        fast_airship = Airship(
            airship_id=Id(uuid7()),
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

        async def mock_create(ticket: Ticket) -> Ticket:
            return ticket

        mock_ticket_repository.create = AsyncMock(side_effect=mock_create)

        # When
        ticket = await ticket_service.purchase_ticket(sample_user, sample_city, fast_airship)

        # Then: 300 x 2 = 600
        assert ticket.cost_points == 600

    async def test_purchase_ticket_calculates_duration_correctly(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_user: User,
        sample_city: City,
    ):
        """티켓 기간이 올바르게 계산된다 (도시 기본 기간 x 비행선 기간 배율)"""
        # Given: 특수 비행선 (기간 배율 0.5배)
        now = datetime.now()
        special_airship = Airship(
            airship_id=Id(uuid7()),
            name="특수 비행선",
            description="빠른 이동",
            image_url=None,
            cost_factor=1,
            duration_factor=1,  # 1배
            display_order=3,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        async def mock_create(ticket: Ticket) -> Ticket:
            return ticket

        mock_ticket_repository.create = AsyncMock(side_effect=mock_create)

        # When
        ticket = await ticket_service.purchase_ticket(sample_user, sample_city, special_airship)

        # Then: 24시간 x 1 = 24시간
        duration_hours = (ticket.arrival_datetime - ticket.departure_datetime).total_seconds() / 3600
        assert duration_hours == 24


class TestTicketServiceComplete:
    """complete 메서드 테스트"""

    async def test_complete_ticket_success(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_ticket: Ticket,
        sample_user: User,
    ):
        """티켓을 성공적으로 완료할 수 있다"""
        # Given: BOARDING 상태의 티켓
        sample_ticket.consume()  # PURCHASED -> BOARDING
        mock_ticket_repository.find_by_id = AsyncMock(return_value=sample_ticket)
        mock_ticket_repository.update = AsyncMock(return_value=sample_ticket)

        # When
        completed_ticket = await ticket_service.complete(sample_user.user_id, sample_ticket.ticket_id)

        # Then
        assert completed_ticket.status == TicketStatus.COMPLETED
        mock_ticket_repository.find_by_id.assert_called_once_with(sample_ticket.ticket_id)
        mock_ticket_repository.update.assert_called_once()

    async def test_complete_raises_error_when_ticket_not_found(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_user: User,
    ):
        """티켓을 찾을 수 없으면 에러가 발생한다"""
        # Given
        ticket_id = Id(uuid7())
        mock_ticket_repository.find_by_id = AsyncMock(return_value=None)

        # When/Then
        with pytest.raises(NotFoundTicketError):
            await ticket_service.complete(sample_user.user_id, ticket_id)

    async def test_complete_raises_error_when_forbidden_user(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_ticket: Ticket,
    ):
        """다른 사용자의 티켓을 완료하려 하면 에러가 발생한다"""
        # Given
        sample_ticket.consume()
        another_user_id = Id(uuid7())
        mock_ticket_repository.find_by_id = AsyncMock(return_value=sample_ticket)

        # When/Then
        with pytest.raises(ForbiddenTicketError):
            await ticket_service.complete(another_user_id, sample_ticket.ticket_id)


class TestTicketServiceCancel:
    """cancel 메서드 테스트"""

    async def test_cancel_ticket_success(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_ticket: Ticket,
        sample_user: User,
    ):
        """티켓을 성공적으로 취소할 수 있다"""
        # Given: PURCHASED 상태의 티켓
        assert sample_ticket.status == TicketStatus.PURCHASED
        mock_ticket_repository.find_by_id = AsyncMock(return_value=sample_ticket)
        mock_ticket_repository.update = AsyncMock(return_value=sample_ticket)

        # When
        cancelled_ticket = await ticket_service.cancel(sample_user.user_id, sample_ticket.ticket_id)

        # Then
        assert cancelled_ticket.status == TicketStatus.CANCELLED
        mock_ticket_repository.find_by_id.assert_called_once_with(sample_ticket.ticket_id)
        mock_ticket_repository.update.assert_called_once()

    async def test_cancel_raises_error_when_ticket_not_found(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_user: User,
    ):
        """티켓을 찾을 수 없으면 에러가 발생한다"""
        # Given
        ticket_id = Id(uuid7())
        mock_ticket_repository.find_by_id = AsyncMock(return_value=None)

        # When/Then
        with pytest.raises(NotFoundTicketError):
            await ticket_service.cancel(sample_user.user_id, ticket_id)

    async def test_cancel_raises_error_when_forbidden_user(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_ticket: Ticket,
    ):
        """다른 사용자의 티켓을 취소하려 하면 에러가 발생한다"""
        # Given
        another_user_id = Id(uuid7())
        mock_ticket_repository.find_by_id = AsyncMock(return_value=sample_ticket)

        # When/Then
        with pytest.raises(ForbiddenTicketError):
            await ticket_service.cancel(another_user_id, sample_ticket.ticket_id)


class TestTicketServiceGetTicketById:
    """get_ticket_by_id 메서드 테스트"""

    async def test_get_ticket_by_id_success(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_ticket: Ticket,
    ):
        """티켓을 ID로 조회할 수 있다"""
        # Given
        mock_ticket_repository.find_by_id = AsyncMock(return_value=sample_ticket)

        # When
        ticket = await ticket_service.get_ticket_by_id(sample_ticket.ticket_id)

        # Then
        assert ticket.ticket_id == sample_ticket.ticket_id
        mock_ticket_repository.find_by_id.assert_called_once_with(sample_ticket.ticket_id)

    async def test_get_ticket_by_id_raises_error_when_not_found(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
    ):
        """티켓을 찾을 수 없으면 에러가 발생한다"""
        # Given
        ticket_id = Id(uuid7())
        mock_ticket_repository.find_by_id = AsyncMock(return_value=None)

        # When/Then
        with pytest.raises(NotFoundTicketError):
            await ticket_service.get_ticket_by_id(ticket_id)

    async def test_get_ticket_by_id_with_user_id_success(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_ticket: Ticket,
        sample_user: User,
    ):
        """사용자 ID를 포함하여 티켓을 조회할 수 있다"""
        # Given
        mock_ticket_repository.find_by_id = AsyncMock(return_value=sample_ticket)

        # When
        ticket = await ticket_service.get_ticket_by_id(sample_ticket.ticket_id, sample_user.user_id)

        # Then
        assert ticket.ticket_id == sample_ticket.ticket_id
        assert ticket.user_id == sample_user.user_id

    async def test_get_ticket_by_id_raises_error_when_forbidden_user(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_ticket: Ticket,
    ):
        """다른 사용자의 티켓을 조회하려 하면 에러가 발생한다"""
        # Given
        another_user_id = Id(uuid7())
        mock_ticket_repository.find_by_id = AsyncMock(return_value=sample_ticket)

        # When/Then
        with pytest.raises(ForbiddenTicketError):
            await ticket_service.get_ticket_by_id(sample_ticket.ticket_id, another_user_id)


class TestTicketServiceGetAllTicketsByUserId:
    """get_all_tickets_by_user_id 메서드 테스트"""

    async def test_get_all_tickets_by_user_id_success(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_ticket: Ticket,
        sample_user: User,
    ):
        """사용자의 모든 티켓을 조회할 수 있다"""
        # Given
        mock_ticket_repository.find_all_by_user_id = AsyncMock(return_value=[sample_ticket])
        mock_ticket_repository.count_by = AsyncMock(return_value=1)

        # When
        tickets, total = await ticket_service.get_all_tickets_by_user_id(sample_user.user_id)

        # Then
        assert len(tickets) == 1
        assert total == 1
        assert tickets[0].user_id == sample_user.user_id
        mock_ticket_repository.find_all_by_user_id.assert_called_once_with(
            user_id=sample_user.user_id, offset=0, limit=100
        )
        mock_ticket_repository.count_by.assert_called_once_with(user_id=sample_user.user_id)

    async def test_get_all_tickets_by_user_id_with_pagination(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_user: User,
    ):
        """pagination 파라미터로 티켓 목록을 조회할 수 있다"""
        # Given
        mock_ticket_repository.find_all_by_user_id = AsyncMock(return_value=[])
        mock_ticket_repository.count_by = AsyncMock(return_value=10)

        # When
        tickets, total = await ticket_service.get_all_tickets_by_user_id(sample_user.user_id, offset=5, limit=5)

        # Then
        assert len(tickets) == 0
        assert total == 10
        mock_ticket_repository.find_all_by_user_id.assert_called_once_with(
            user_id=sample_user.user_id, offset=5, limit=5
        )

    async def test_get_all_tickets_by_user_id_returns_empty_list(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_user: User,
    ):
        """티켓이 없으면 빈 리스트를 반환한다"""
        # Given
        mock_ticket_repository.find_all_by_user_id = AsyncMock(return_value=[])
        mock_ticket_repository.count_by = AsyncMock(return_value=0)

        # When
        tickets, total = await ticket_service.get_all_tickets_by_user_id(sample_user.user_id)

        # Then
        assert tickets == []
        assert total == 0


class TestTicketServiceGetAllTicketsByUserIdAndStatus:
    """get_all_tickets_by_user_id_and_status 메서드 테스트"""

    async def test_get_all_tickets_by_user_id_and_status_success(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_ticket: Ticket,
        sample_user: User,
    ):
        """사용자의 특정 상태 티켓을 조회할 수 있다"""
        # Given
        sample_ticket.consume()  # BOARDING 상태로 변경
        mock_ticket_repository.find_all_by_user_id_and_status = AsyncMock(return_value=[sample_ticket])
        mock_ticket_repository.count_by = AsyncMock(return_value=1)

        # When
        tickets, total = await ticket_service.get_all_tickets_by_user_id_and_status(
            sample_user.user_id, TicketStatus.BOARDING
        )

        # Then
        assert len(tickets) == 1
        assert total == 1
        assert tickets[0].status == TicketStatus.BOARDING
        mock_ticket_repository.find_all_by_user_id_and_status.assert_called_once_with(
            user_id=sample_user.user_id, status=TicketStatus.BOARDING, offset=0, limit=100
        )
        mock_ticket_repository.count_by.assert_called_once_with(
            user_id=sample_user.user_id, status=TicketStatus.BOARDING
        )

    async def test_get_all_tickets_by_user_id_and_status_with_pagination(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_user: User,
    ):
        """pagination 파라미터로 특정 상태 티켓을 조회할 수 있다"""
        # Given
        mock_ticket_repository.find_all_by_user_id_and_status = AsyncMock(return_value=[])
        mock_ticket_repository.count_by = AsyncMock(return_value=15)

        # When
        tickets, total = await ticket_service.get_all_tickets_by_user_id_and_status(
            sample_user.user_id, TicketStatus.COMPLETED, offset=10, limit=5
        )

        # Then
        assert len(tickets) == 0
        assert total == 15
        mock_ticket_repository.find_all_by_user_id_and_status.assert_called_once_with(
            user_id=sample_user.user_id, status=TicketStatus.COMPLETED, offset=10, limit=5
        )

    async def test_get_all_tickets_by_user_id_and_status_returns_empty_list(
        self,
        ticket_service: TicketService,
        mock_ticket_repository: MagicMock,
        sample_user: User,
    ):
        """해당 상태의 티켓이 없으면 빈 리스트를 반환한다"""
        # Given
        mock_ticket_repository.find_all_by_user_id_and_status = AsyncMock(return_value=[])
        mock_ticket_repository.count_by = AsyncMock(return_value=0)

        # When
        tickets, total = await ticket_service.get_all_tickets_by_user_id_and_status(
            sample_user.user_id, TicketStatus.CANCELLED
        )

        # Then
        assert tickets == []
        assert total == 0
