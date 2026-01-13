"""Ticket Use Cases Integration Tests."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.application.use_cases.tickets.cancel_ticket import CancelTicketUseCase
from bzero.application.use_cases.tickets.get_current_boarding_ticket import GetCurrentBoardingTicketUseCase
from bzero.application.use_cases.tickets.get_ticket_detail import GetTicketDetailUseCase
from bzero.application.use_cases.tickets.get_tickets_by_user import GetTicketsByUserUseCase
from bzero.application.use_cases.tickets.purchase_ticket import PurchaseTicketUseCase
from bzero.core.settings import get_settings
from bzero.domain.entities import Airship, City, Ticket, User, UserIdentity
from bzero.domain.errors import (
    CityNotFoundError,
    ForbiddenTicketError,
    InsufficientBalanceError,
    InvalidAirshipStatusError,
    InvalidCityStatusError,
    NotFoundAirshipError,
    NotFoundTicketError,
    NotFoundUserError,
)
from bzero.domain.repositories.point_transaction import TransactionFilter
from bzero.domain.services import AirshipService, CityService, PointTransactionService, TicketService, UserService
from bzero.domain.value_objects import (
    AuthProvider,
    Balance,
    Email,
    Id,
    Nickname,
    Profile,
    TicketStatus,
    TransactionReason,
    TransactionStatus,
    TransactionType,
)
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.point_transaction_model import PointTransactionModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.airship import SqlAlchemyAirshipRepository
from bzero.infrastructure.repositories.city import SqlAlchemyCityRepository
from bzero.infrastructure.repositories.point_transaction import SqlAlchemyPointTransactionRepository
from bzero.infrastructure.repositories.ticket import SqlAlchemyTicketRepository
from bzero.infrastructure.repositories.user import SqlAlchemyUserRepository
from bzero.infrastructure.repositories.user_identity import SqlAlchemyUserIdentityRepository


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone"""
    return get_settings().timezone


@pytest.fixture
def user_repository(test_session: AsyncSession) -> SqlAlchemyUserRepository:
    """UserRepository fixture를 생성합니다."""
    return SqlAlchemyUserRepository(test_session)


@pytest.fixture
def user_identity_repository(test_session: AsyncSession) -> SqlAlchemyUserIdentityRepository:
    """UserIdentityRepository fixture를 생성합니다."""
    return SqlAlchemyUserIdentityRepository(test_session)


@pytest.fixture
def city_repository(test_session: AsyncSession) -> SqlAlchemyCityRepository:
    """CityRepository fixture를 생성합니다."""
    return SqlAlchemyCityRepository(test_session)


@pytest.fixture
def airship_repository(test_session: AsyncSession) -> SqlAlchemyAirshipRepository:
    """AirshipRepository fixture를 생성합니다."""
    return SqlAlchemyAirshipRepository(test_session)


@pytest.fixture
def ticket_repository(test_session: AsyncSession) -> SqlAlchemyTicketRepository:
    """TicketRepository fixture를 생성합니다."""
    return SqlAlchemyTicketRepository(test_session)


@pytest.fixture
def point_transaction_repository(test_session: AsyncSession) -> SqlAlchemyPointTransactionRepository:
    """PointTransactionRepository fixture를 생성합니다."""
    return SqlAlchemyPointTransactionRepository(test_session)


@pytest.fixture
def user_service(
    user_repository: SqlAlchemyUserRepository,
    user_identity_repository: SqlAlchemyUserIdentityRepository,
    timezone: ZoneInfo,
) -> UserService:
    """UserService fixture를 생성합니다."""
    return UserService(user_repository, user_identity_repository, timezone)


@pytest.fixture
def city_service(city_repository: SqlAlchemyCityRepository) -> CityService:
    """CityService fixture를 생성합니다."""
    return CityService(city_repository)


@pytest.fixture
def airship_service(airship_repository: SqlAlchemyAirshipRepository) -> AirshipService:
    """AirshipService fixture를 생성합니다."""
    return AirshipService(airship_repository)


@pytest.fixture
def ticket_service(ticket_repository: SqlAlchemyTicketRepository, timezone: ZoneInfo) -> TicketService:
    """TicketService fixture를 생성합니다."""
    return TicketService(ticket_repository, timezone)


@pytest.fixture
def point_transaction_service(
    user_repository: SqlAlchemyUserRepository,
    point_transaction_repository: SqlAlchemyPointTransactionRepository,
) -> PointTransactionService:
    """PointTransactionService fixture를 생성합니다."""
    return PointTransactionService(user_repository, point_transaction_repository)


@pytest_asyncio.fixture
async def test_user(test_session: AsyncSession, timezone: ZoneInfo) -> User:
    """테스트용 사용자를 생성합니다 (초기 잔액 1000)."""
    now = datetime.now(timezone)
    user_id = uuid7()
    initial_points = 1000

    # UserModel을 직접 생성하여 DB에 저장
    user_model = UserModel(
        user_id=user_id,
        email="test@example.com",
        nickname="테스트유저",
        profile_emoji="😎",
        current_points=initial_points,  # 티켓 구매를 위한 초기 잔액
        created_at=now,
        updated_at=now,
    )
    test_session.add(user_model)
    await test_session.flush()

    # 가입 보너스 포인트 거래 생성 (실제 잔액 계산을 위해)
    signup_bonus_transaction = PointTransactionModel(
        point_transaction_id=uuid7(),
        user_id=user_id,
        transaction_type=TransactionType.EARN.value,
        amount=initial_points,
        reason=TransactionReason.SIGNED_UP.value,
        balance_before=0,
        balance_after=initial_points,
        status=TransactionStatus.COMPLETED.value,
        created_at=now,
        updated_at=now,
    )
    test_session.add(signup_bonus_transaction)
    await test_session.flush()

    # User 엔티티로 변환
    return User(
        user_id=Id(user_model.user_id),
        email=Email(user_model.email) if user_model.email else None,
        nickname=Nickname(user_model.nickname) if user_model.nickname else None,
        profile=Profile(user_model.profile_emoji) if user_model.profile_emoji else None,
        current_points=Balance(user_model.current_points),
        created_at=user_model.created_at,
        updated_at=user_model.updated_at,
        deleted_at=user_model.deleted_at,
    )


@pytest_asyncio.fixture
async def test_user_identity(
    user_identity_repository: SqlAlchemyUserIdentityRepository,
    test_user: User,
    timezone: ZoneInfo,
) -> UserIdentity:
    """테스트용 사용자 인증 정보를 생성합니다."""
    now = datetime.now(timezone)
    identity = UserIdentity(
        identity_id=Id(),
        user_id=test_user.user_id,
        provider=AuthProvider.EMAIL,
        provider_user_id="test-provider-user-123",
        created_at=now,
        updated_at=now,
    )
    return await user_identity_repository.create(identity)


@pytest_asyncio.fixture
async def test_city(test_session: AsyncSession, timezone: ZoneInfo) -> City:
    """테스트용 도시를 생성합니다."""
    now = datetime.now(timezone)

    # CityModel을 직접 생성하여 DB에 저장
    city_model = CityModel(
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
    test_session.add(city_model)
    await test_session.flush()

    # City 엔티티로 변환
    return City(
        city_id=Id(city_model.city_id),
        name=city_model.name,
        theme=city_model.theme,
        description=city_model.description,
        image_url=city_model.image_url,
        base_cost_points=city_model.base_cost_points,
        base_duration_minutes=city_model.base_duration_minutes,
        is_active=city_model.is_active,
        display_order=city_model.display_order,
        created_at=city_model.created_at,
        updated_at=city_model.updated_at,
    )


@pytest_asyncio.fixture
async def test_airship(test_session: AsyncSession, timezone: ZoneInfo) -> Airship:
    """테스트용 비행선을 생성합니다."""
    now = datetime.now(timezone)

    # AirshipModel을 직접 생성하여 DB에 저장
    airship_model = AirshipModel(
        airship_id=uuid7(),
        name="일반 비행선",
        description="느긋하게 여행하는 일반 비행선",
        image_url="https://example.com/regular.jpg",
        cost_factor=1,
        duration_factor=1,
        is_active=True,
        display_order=1,
        created_at=now,
        updated_at=now,
    )
    test_session.add(airship_model)
    await test_session.flush()

    # Airship 엔티티로 변환
    return Airship(
        airship_id=Id(airship_model.airship_id),
        name=airship_model.name,
        description=airship_model.description,
        image_url=airship_model.image_url,
        cost_factor=airship_model.cost_factor,
        duration_factor=airship_model.duration_factor,
        is_active=airship_model.is_active,
        display_order=airship_model.display_order,
        created_at=airship_model.created_at,
        updated_at=airship_model.updated_at,
    )


# =============================================================================
# Use Case Fixtures (모듈 레벨)
# =============================================================================


@pytest.fixture
def purchase_ticket_use_case(
    test_session: AsyncSession,
    user_service: UserService,
    city_service: CityService,
    airship_service: AirshipService,
    ticket_service: TicketService,
    point_transaction_service: PointTransactionService,
) -> PurchaseTicketUseCase:
    """PurchaseTicketUseCase fixture를 생성합니다."""
    return PurchaseTicketUseCase(
        test_session,
        user_service,
        city_service,
        airship_service,
        ticket_service,
        point_transaction_service,
    )


@pytest.fixture
def cancel_ticket_use_case(
    test_session: AsyncSession,
    user_service: UserService,
    city_service: CityService,
    airship_service: AirshipService,
    ticket_service: TicketService,
    point_transaction_service: PointTransactionService,
) -> CancelTicketUseCase:
    """CancelTicketUseCase fixture를 생성합니다."""
    return CancelTicketUseCase(
        test_session,
        user_service,
        city_service,
        airship_service,
        ticket_service,
        point_transaction_service,
    )


@pytest.fixture
def get_ticket_detail_use_case(
    user_service: UserService,
    ticket_service: TicketService,
) -> GetTicketDetailUseCase:
    """GetTicketDetailUseCase fixture를 생성합니다."""
    return GetTicketDetailUseCase(user_service, ticket_service)


@pytest.fixture
def get_tickets_by_user_use_case(
    user_service: UserService,
    ticket_service: TicketService,
) -> GetTicketsByUserUseCase:
    """GetTicketsByUserUseCase fixture를 생성합니다."""
    return GetTicketsByUserUseCase(user_service, ticket_service)


@pytest.fixture
def get_current_boarding_ticket_use_case(
    user_service: UserService,
    ticket_service: TicketService,
) -> GetCurrentBoardingTicketUseCase:
    """GetCurrentBoardingTicketUseCase fixture를 생성합니다."""
    return GetCurrentBoardingTicketUseCase(user_service, ticket_service)


@pytest_asyncio.fixture
async def boarding_ticket_result(
    purchase_ticket_use_case: PurchaseTicketUseCase,
    test_user_identity: UserIdentity,
    test_city: City,
    test_airship: Airship,
):
    """PurchaseTicketUseCase를 통해 BOARDING 상태의 티켓을 생성합니다."""
    return await purchase_ticket_use_case.execute(
        provider=test_user_identity.provider.value,
        provider_user_id=test_user_identity.provider_user_id,
        city_id=str(test_city.city_id.value),
        airship_id=str(test_airship.airship_id.value),
    )


@pytest_asyncio.fixture
async def purchased_ticket(
    test_user: User,
    test_city: City,
    test_airship: Airship,
    ticket_repository: SqlAlchemyTicketRepository,
    timezone: ZoneInfo,
):
    """PURCHASED 상태의 티켓을 직접 생성합니다."""
    now = datetime.now(timezone)

    # Ticket.create()로 생성하면 자동으로 PURCHASED 상태
    ticket = Ticket.create(
        user_id=test_user.user_id,
        city_snapshot=test_city.snapshot(),
        airship_snapshot=test_airship.snapshot(),
        cost_points=test_city.base_cost_points * test_airship.cost_factor,
        departure_datetime=now,
        arrival_datetime=now + timedelta(minutes=test_city.base_duration_minutes),
        created_at=now,
        updated_at=now,
    )
    return await ticket_repository.create(ticket)


# =============================================================================
# PurchaseTicketUseCase Tests
# =============================================================================


class TestPurchaseTicketUseCase:
    """PurchaseTicketUseCase 통합 테스트."""

    @pytest.mark.asyncio
    async def test_purchase_ticket_success(
        self,
        purchase_ticket_use_case: PurchaseTicketUseCase,
        test_user_identity: UserIdentity,
        test_user: User,
        test_city: City,
        test_airship: Airship,
        user_repository: SqlAlchemyUserRepository,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
    ):
        """티켓을 정상적으로 구매하고 포인트가 차감되어야 합니다."""
        # Given: 사용자, 도시, 비행선이 준비됨
        initial_balance = test_user.current_points.value
        expected_cost = test_city.base_cost_points * test_airship.cost_factor

        # When: 티켓 구매
        result = await purchase_ticket_use_case.execute(
            provider=test_user_identity.provider.value,
            provider_user_id=test_user_identity.provider_user_id,
            city_id=str(test_city.city_id.value),
            airship_id=str(test_airship.airship_id.value),
        )

        # Then: 티켓이 생성되고 상태는 BOARDING
        assert result.ticket_id is not None
        assert result.status == TicketStatus.BOARDING.value
        assert result.cost_points == expected_cost
        assert result.city_snapshot.name == test_city.name
        assert result.airship_snapshot.name == test_airship.name

        # Then: 사용자 잔액이 차감됨
        updated_user = await user_repository.find_by_user_id(test_user.user_id)
        assert updated_user is not None
        assert updated_user.current_points.value == initial_balance - expected_cost

        # Then: 포인트 거래 내역이 생성됨 (가입 보너스 + 티켓 구매)
        filter_by_user = TransactionFilter(user_id=test_user.user_id)
        transactions = await point_transaction_repository.find_by_filter(filter_by_user, limit=100)
        assert len(transactions) == 2  # 가입 보너스 + 티켓 구매
        # SPEND 타입의 거래가 티켓 구매 거래
        spend_transactions = [t for t in transactions if t.transaction_type == TransactionType.SPEND]
        assert len(spend_transactions) == 1
        purchase_transaction = spend_transactions[0]
        assert purchase_transaction.amount == expected_cost

    @pytest.mark.asyncio
    async def test_purchase_ticket_with_nonexistent_user(
        self,
        purchase_ticket_use_case: PurchaseTicketUseCase,
        test_city: City,
        test_airship: Airship,
    ):
        """존재하지 않는 사용자로 티켓 구매 시 에러가 발생해야 합니다."""
        # When/Then: 존재하지 않는 사용자로 티켓 구매
        with pytest.raises(NotFoundUserError):
            await purchase_ticket_use_case.execute(
                provider="email",
                provider_user_id="nonexistent-user",
                city_id=str(test_city.city_id.value),
                airship_id=str(test_airship.airship_id.value),
            )

    @pytest.mark.asyncio
    async def test_purchase_ticket_with_nonexistent_city(
        self,
        purchase_ticket_use_case: PurchaseTicketUseCase,
        test_user_identity: UserIdentity,
        test_airship: Airship,
    ):
        """존재하지 않는 도시로 티켓 구매 시 에러가 발생해야 합니다."""
        # Given: 존재하지 않는 도시 ID
        nonexistent_city_id = Id()

        # When/Then: 존재하지 않는 도시로 티켓 구매
        with pytest.raises(CityNotFoundError):
            await purchase_ticket_use_case.execute(
                provider=test_user_identity.provider.value,
                provider_user_id=test_user_identity.provider_user_id,
                city_id=str(nonexistent_city_id.value),
                airship_id=str(test_airship.airship_id.value),
            )

    @pytest.mark.asyncio
    async def test_purchase_ticket_with_nonexistent_airship(
        self,
        purchase_ticket_use_case: PurchaseTicketUseCase,
        test_user_identity: UserIdentity,
        test_city: City,
    ):
        """존재하지 않는 비행선으로 티켓 구매 시 에러가 발생해야 합니다."""
        # Given: 존재하지 않는 비행선 ID
        nonexistent_airship_id = Id()

        # When/Then: 존재하지 않는 비행선으로 티켓 구매
        with pytest.raises(NotFoundAirshipError):
            await purchase_ticket_use_case.execute(
                provider=test_user_identity.provider.value,
                provider_user_id=test_user_identity.provider_user_id,
                city_id=str(test_city.city_id.value),
                airship_id=str(nonexistent_airship_id.value),
            )

    @pytest.mark.asyncio
    async def test_purchase_ticket_with_insufficient_balance(
        self,
        purchase_ticket_use_case: PurchaseTicketUseCase,
        test_user_identity: UserIdentity,
        test_city: City,
        test_airship: Airship,
        user_repository: SqlAlchemyUserRepository,
        test_user: User,
    ):
        """포인트가 부족한 경우 에러가 발생해야 합니다."""
        # Given: 사용자 잔액을 0으로 설정
        test_user.current_points = Balance(0)
        await user_repository.update(test_user)

        # When/Then: 포인트 부족 시 에러 발생
        with pytest.raises(InsufficientBalanceError):
            await purchase_ticket_use_case.execute(
                provider=test_user_identity.provider.value,
                provider_user_id=test_user_identity.provider_user_id,
                city_id=str(test_city.city_id.value),
                airship_id=str(test_airship.airship_id.value),
            )

    @pytest.mark.asyncio
    async def test_purchase_ticket_with_inactive_city(
        self,
        purchase_ticket_use_case: PurchaseTicketUseCase,
        test_user_identity: UserIdentity,
        test_airship: Airship,
        test_session: AsyncSession,
        timezone: ZoneInfo,
    ):
        """비활성화된 도시로 티켓 구매 시 에러가 발생해야 합니다."""
        # Given: 비활성화된 도시를 직접 생성
        now = datetime.now(timezone)

        inactive_city_model = CityModel(
            city_id=uuid7(),
            name="비활성 도시",
            theme="테마",
            description="비활성화된 도시입니다",
            image_url="https://example.com/inactive.jpg",
            base_cost_points=300,
            base_duration_minutes=24,
            is_active=False,  # 비활성화
            display_order=99,
            created_at=now,
            updated_at=now,
        )
        test_session.add(inactive_city_model)
        await test_session.flush()

        # When/Then: 비활성화된 도시로 티켓 구매 시 에러 발생
        with pytest.raises(InvalidCityStatusError):
            await purchase_ticket_use_case.execute(
                provider=test_user_identity.provider.value,
                provider_user_id=test_user_identity.provider_user_id,
                city_id=str(inactive_city_model.city_id),
                airship_id=str(test_airship.airship_id.value),
            )

    @pytest.mark.asyncio
    async def test_purchase_ticket_with_inactive_airship(
        self,
        purchase_ticket_use_case: PurchaseTicketUseCase,
        test_user_identity: UserIdentity,
        test_city: City,
        test_session: AsyncSession,
        timezone: ZoneInfo,
    ):
        """비활성화된 비행선으로 티켓 구매 시 에러가 발생해야 합니다."""
        # Given: 비활성화된 비행선을 직접 생성
        now = datetime.now(timezone)

        inactive_airship_model = AirshipModel(
            airship_id=uuid7(),
            name="비활성 비행선",
            description="비활성화된 비행선입니다",
            image_url="https://example.com/inactive.jpg",
            cost_factor=1,
            duration_factor=1,
            is_active=False,  # 비활성화
            display_order=99,
            created_at=now,
            updated_at=now,
        )
        test_session.add(inactive_airship_model)
        await test_session.flush()

        # When/Then: 비활성화된 비행선으로 티켓 구매 시 에러 발생
        with pytest.raises(InvalidAirshipStatusError):
            await purchase_ticket_use_case.execute(
                provider=test_user_identity.provider.value,
                provider_user_id=test_user_identity.provider_user_id,
                city_id=str(test_city.city_id.value),
                airship_id=str(inactive_airship_model.airship_id),
            )


# =============================================================================
# CancelTicketUseCase Tests
# =============================================================================


class TestCancelTicketUseCase:
    """CancelTicketUseCase 통합 테스트."""

    @pytest.mark.asyncio
    async def test_cancel_ticket_success(
        self,
        cancel_ticket_use_case: CancelTicketUseCase,
        test_user_identity: UserIdentity,
        test_user: User,
        purchased_ticket,
        user_repository: SqlAlchemyUserRepository,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
    ):
        """티켓을 정상적으로 취소하고 포인트가 환불되어야 합니다."""
        # Given: PURCHASED 상태의 티켓
        initial_balance = test_user.current_points.value
        ticket_cost = purchased_ticket.cost_points

        # When: 티켓 취소
        result = await cancel_ticket_use_case.execute(
            provider=test_user_identity.provider.value,
            provider_user_id=test_user_identity.provider_user_id,
            ticket_id=str(purchased_ticket.ticket_id.value),
        )

        # Then: 티켓 상태가 CANCELLED로 변경됨
        assert result.status == TicketStatus.CANCELLED.value

        # Then: 사용자 잔액이 환불됨
        updated_user = await user_repository.find_by_user_id(test_user.user_id)
        assert updated_user is not None
        assert updated_user.current_points.value == initial_balance + ticket_cost

        # Then: 환불 거래 내역이 생성됨 (가입 보너스 거래 + 환불 거래)
        filter_by_user = TransactionFilter(user_id=test_user.user_id)
        transactions = await point_transaction_repository.find_by_filter(filter_by_user, limit=100)
        assert len(transactions) == 2  # 가입 보너스 + 환불 거래
        # EARN 타입 중 SIGNED_UP이 아닌 거래가 환불 거래 (또는 reason으로 구분)
        # CancelTicketUseCase는 EARN 거래를 생성하므로 2개의 EARN 거래가 있음
        earn_transactions = [t for t in transactions if t.transaction_type == TransactionType.EARN]
        assert len(earn_transactions) == 2  # 가입 보너스 + 환불
        # 환불 거래는 REFUND reason
        refund_transactions = [t for t in earn_transactions if t.reason == TransactionReason.REFUND]
        assert len(refund_transactions) == 1
        refund_transaction = refund_transactions[0]
        assert refund_transaction.amount == ticket_cost

    @pytest.mark.asyncio
    async def test_cancel_ticket_with_nonexistent_ticket(
        self,
        cancel_ticket_use_case: CancelTicketUseCase,
        test_user_identity: UserIdentity,
    ):
        """존재하지 않는 티켓 취소 시 에러가 발생해야 합니다."""
        # Given: 존재하지 않는 티켓 ID
        nonexistent_ticket_id = Id()

        # When/Then: 존재하지 않는 티켓 취소 시 에러 발생
        with pytest.raises(NotFoundTicketError):
            await cancel_ticket_use_case.execute(
                provider=test_user_identity.provider.value,
                provider_user_id=test_user_identity.provider_user_id,
                ticket_id=str(nonexistent_ticket_id.value),
            )


# =============================================================================
# GetTicketDetailUseCase Tests
# =============================================================================


class TestGetTicketDetailUseCase:
    """GetTicketDetailUseCase 통합 테스트."""

    @pytest.mark.asyncio
    async def test_get_ticket_detail_success(
        self,
        get_ticket_detail_use_case: GetTicketDetailUseCase,
        test_user_identity: UserIdentity,
        purchased_ticket,
    ):
        """티켓 상세 정보를 정상적으로 조회할 수 있어야 합니다."""
        # When: 티켓 상세 조회
        result = await get_ticket_detail_use_case.execute(
            provider=test_user_identity.provider.value,
            provider_user_id=test_user_identity.provider_user_id,
            ticket_id=str(purchased_ticket.ticket_id.value),
        )

        # Then: 티켓 정보가 올바르게 반환됨 (UUID 형식 정규화하여 비교)
        assert result.ticket_id.replace("-", "") == str(purchased_ticket.ticket_id.value).replace("-", "")
        assert result.status == purchased_ticket.status.value
        assert result.cost_points == purchased_ticket.cost_points

    @pytest.mark.asyncio
    async def test_get_ticket_detail_of_other_user(
        self,
        get_ticket_detail_use_case: GetTicketDetailUseCase,
        purchased_ticket,
        user_identity_repository: SqlAlchemyUserIdentityRepository,
        user_repository: SqlAlchemyUserRepository,
        timezone: ZoneInfo,
    ):
        """다른 사용자의 티켓 조회 시 에러가 발생해야 합니다."""
        # Given: 다른 사용자 생성
        now = datetime.now(timezone)
        other_user = User(
            user_id=Id(),
            email=Email("other@example.com"),
            nickname=Nickname("다른유저"),
            profile=Profile("😊"),  # 허용된 이모지 사용
            current_points=Balance(1000),
            created_at=now,
            updated_at=now,
        )
        other_user = await user_repository.create(other_user)

        other_identity = UserIdentity(
            identity_id=Id(),
            user_id=other_user.user_id,
            provider=AuthProvider.EMAIL,
            provider_user_id="other-provider-user-789",
            created_at=now,
            updated_at=now,
        )
        other_identity = await user_identity_repository.create(other_identity)

        # When/Then: 다른 사용자가 티켓 조회 시도 시 에러 발생
        with pytest.raises(ForbiddenTicketError):
            await get_ticket_detail_use_case.execute(
                provider=other_identity.provider.value,
                provider_user_id=other_identity.provider_user_id,
                ticket_id=str(purchased_ticket.ticket_id.value),
            )


# =============================================================================
# GetTicketsByUserUseCase Tests
# =============================================================================


class TestGetTicketsByUserUseCase:
    """GetTicketsByUserUseCase 통합 테스트."""

    @pytest_asyncio.fixture
    async def multiple_tickets(
        self,
        test_user: User,
        test_city: City,
        test_airship: Airship,
        ticket_repository: SqlAlchemyTicketRepository,
        timezone: ZoneInfo,
    ):
        """여러 개의 티켓을 생성합니다."""
        now = datetime.now(timezone)

        tickets = []
        for i in range(5):
            ticket = Ticket.create(
                user_id=test_user.user_id,
                city_snapshot=test_city.snapshot(),
                airship_snapshot=test_airship.snapshot(),
                cost_points=test_city.base_cost_points * test_airship.cost_factor,
                departure_datetime=now + timedelta(hours=i),
                arrival_datetime=now + timedelta(hours=i, minutes=test_city.base_duration_minutes),
                created_at=now,
                updated_at=now,
            )
            tickets.append(await ticket_repository.create(ticket))
        return tickets

    @pytest.mark.asyncio
    async def test_get_tickets_by_user_success(
        self,
        get_tickets_by_user_use_case: GetTicketsByUserUseCase,
        test_user_identity: UserIdentity,
        multiple_tickets,
    ):
        """사용자의 티켓 목록을 정상적으로 조회할 수 있어야 합니다."""
        # When: 티켓 목록 조회 (전체)
        result = await get_tickets_by_user_use_case.execute(
            provider=test_user_identity.provider.value,
            provider_user_id=test_user_identity.provider_user_id,
            offset=0,
            limit=100,
        )

        # Then: 모든 티켓이 반환됨
        assert result.total == 5
        assert len(result.items) == 5

    @pytest.mark.asyncio
    async def test_get_tickets_by_user_with_pagination(
        self,
        get_tickets_by_user_use_case: GetTicketsByUserUseCase,
        test_user_identity: UserIdentity,
        multiple_tickets,
    ):
        """pagination이 정상적으로 동작해야 합니다."""
        # When: 티켓 목록 조회 (페이지네이션)
        result = await get_tickets_by_user_use_case.execute(
            provider=test_user_identity.provider.value,
            provider_user_id=test_user_identity.provider_user_id,
            offset=2,
            limit=2,
        )

        # Then: 페이지네이션이 올바르게 적용됨
        assert result.total == 5
        assert len(result.items) == 2
        assert result.offset == 2
        assert result.limit == 2


# =============================================================================
# GetCurrentBoardingTicketUseCase Tests
# =============================================================================


class TestGetCurrentBoardingTicketUseCase:
    """GetCurrentBoardingTicketUseCase 통합 테스트."""

    @pytest_asyncio.fixture
    async def boarding_ticket(
        self,
        test_user: User,
        test_city: City,
        test_airship: Airship,
        ticket_repository: SqlAlchemyTicketRepository,
        timezone: ZoneInfo,
    ):
        """BOARDING 상태의 티켓을 생성합니다."""
        now = datetime.now(timezone)

        ticket = Ticket.create(
            user_id=test_user.user_id,
            city_snapshot=test_city.snapshot(),
            airship_snapshot=test_airship.snapshot(),
            cost_points=test_city.base_cost_points * test_airship.cost_factor,
            departure_datetime=now,
            arrival_datetime=now + timedelta(minutes=test_city.base_duration_minutes),
            created_at=now,
            updated_at=now,
        )
        # PURCHASED 상태로 생성된 티켓을 BOARDING으로 변경
        ticket.consume()
        return await ticket_repository.create(ticket)

    @pytest.mark.asyncio
    async def test_get_current_boarding_ticket_success(
        self,
        get_current_boarding_ticket_use_case: GetCurrentBoardingTicketUseCase,
        test_user_identity: UserIdentity,
        boarding_ticket,
    ):
        """현재 탑승 중인 티켓을 정상적으로 조회할 수 있어야 합니다."""
        # When: 현재 탑승 중인 티켓 조회
        result = await get_current_boarding_ticket_use_case.execute(
            provider=test_user_identity.provider.value,
            provider_user_id=test_user_identity.provider_user_id,
        )

        # Then: BOARDING 상태의 티켓이 반환됨 (UUID 형식 정규화하여 비교)
        assert result.ticket_id.replace("-", "") == str(boarding_ticket.ticket_id.value).replace("-", "")
        assert result.status == TicketStatus.BOARDING.value

    @pytest.mark.asyncio
    async def test_get_current_boarding_ticket_when_no_boarding_ticket(
        self,
        get_current_boarding_ticket_use_case: GetCurrentBoardingTicketUseCase,
        test_user_identity: UserIdentity,
    ):
        """탑승 중인 티켓이 없을 때 에러가 발생해야 합니다."""
        # When/Then: 탑승 중인 티켓이 없을 때 에러 발생
        with pytest.raises(NotFoundTicketError):
            await get_current_boarding_ticket_use_case.execute(
                provider=test_user_identity.provider.value,
                provider_user_id=test_user_identity.provider_user_id,
            )
