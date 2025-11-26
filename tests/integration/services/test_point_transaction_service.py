"""PointTransactionService Integration Tests."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.core.settings import get_settings
from bzero.domain.entities.user import User
from bzero.domain.errors import DuplicatedRewardError, InvalidAmountError
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.value_objects import Balance, Email, Id, Nickname, Profile
from bzero.domain.value_objects.point_transaction import TransactionReason, TransactionReference, TransactionType
from bzero.infrastructure.repositories.point_transaction import SqlAlchemyPointTransactionRepository
from bzero.infrastructure.repositories.user import SqlAlchemyUserRepository


@pytest.fixture
def user_repository(test_session: AsyncSession) -> SqlAlchemyUserRepository:
    """UserRepository fixture를 생성합니다."""
    return SqlAlchemyUserRepository(test_session)


@pytest.fixture
def point_transaction_repository(test_session: AsyncSession) -> SqlAlchemyPointTransactionRepository:
    """PointTransactionRepository fixture를 생성합니다."""
    return SqlAlchemyPointTransactionRepository(test_session)


@pytest.fixture
def point_transaction_service(
    user_repository: SqlAlchemyUserRepository,
    point_transaction_repository: SqlAlchemyPointTransactionRepository,
) -> PointTransactionService:
    """PointTransactionService fixture를 생성합니다."""
    return PointTransactionService(user_repository, point_transaction_repository)


@pytest.fixture
async def test_user(user_repository: SqlAlchemyUserRepository) -> User:
    """테스트용 사용자를 생성합니다 (초기 잔액 0)."""
    user = User(
        user_id=Id(),
        email=Email("test@example.com"),
        nickname=Nickname("테스트유저"),
        profile=Profile("🎉"),
        current_points=Balance(0),
        created_at=datetime.now(get_settings().timezone),
        updated_at=datetime.now(get_settings().timezone),
        deleted_at=None,
    )
    return await user_repository.create(user)


class TestPointTransactionServiceEarnBy:
    """PointTransactionService.earn_by() 메서드 테스트."""

    async def test_earn_by_success(
        self,
        point_transaction_service: PointTransactionService,
        test_user: User,
    ):
        """포인트를 정상적으로 적립할 수 있어야 합니다."""
        # Given: 초기 잔액이 0인 사용자
        initial_balance = test_user.current_points.value

        # When: 1000 포인트 적립
        updated_user, transaction = await point_transaction_service.earn_by(
            user=test_user,
            amount=1000,
            reason=TransactionReason.SIGNED_UP,
            reference_type=TransactionReference.USERS,
            reference_id=test_user.user_id,
            description="회원가입 보너스",
        )

        # Then: 사용자 잔액이 업데이트됨
        assert updated_user.current_points.value == initial_balance + 1000
        # Then: 거래가 생성됨
        assert transaction.transaction_type == TransactionType.EARN
        assert transaction.amount == 1000
        assert transaction.balance_before.value == initial_balance
        assert transaction.balance_after.value == initial_balance + 1000
        assert transaction.user_id == test_user.user_id

    async def test_earn_by_with_invalid_amount(
        self,
        point_transaction_service: PointTransactionService,
        test_user: User,
    ):
        """음수 금액으로 적립하려고 하면 에러가 발생해야 합니다."""
        # When & Then: 음수 금액으로 적립 시도
        with pytest.raises(InvalidAmountError):
            await point_transaction_service.earn_by(
                user=test_user,
                amount=-100,
                reason=TransactionReason.SIGNED_UP,
                reference_type=None,
                reference_id=None,
                description=None,
            )

        # When & Then: 0 금액으로 적립 시도
        with pytest.raises(InvalidAmountError):
            await point_transaction_service.earn_by(
                user=test_user,
                amount=0,
                reason=TransactionReason.SIGNED_UP,
                reference_type=None,
                reference_id=None,
                description=None,
            )

    async def test_earn_by_prevents_duplicate_reward(
        self,
        point_transaction_service: PointTransactionService,
        test_user: User,
    ):
        """중복 지급을 방지해야 합니다."""
        # Given: 일기 작성 보상을 지급
        diary_id = Id()
        await point_transaction_service.earn_by(
            user=test_user,
            amount=50,
            reason=TransactionReason.DIARY,
            reference_type=TransactionReference.DIARIES,
            reference_id=diary_id,
            description="일기 작성 보상",
        )

        # When & Then: 같은 일기에 대한 보상을 다시 지급하려고 하면 에러 발생
        with pytest.raises(DuplicatedRewardError):
            await point_transaction_service.earn_by(
                user=test_user,
                amount=50,
                reason=TransactionReason.DIARY,
                reference_type=TransactionReference.DIARIES,
                reference_id=diary_id,
                description="일기 작성 보상",
            )

    async def test_earn_by_updates_user_balance_correctly(
        self,
        point_transaction_service: PointTransactionService,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        test_user: User,
    ):
        """적립 후 사용자 잔액이 실제 거래 내역과 일치해야 합니다."""
        # When: 여러 번 포인트 적립
        await point_transaction_service.earn_by(
            user=test_user,
            amount=1000,
            reason=TransactionReason.SIGNED_UP,
            reference_type=TransactionReference.USERS,
            reference_id=test_user.user_id,
            description="회원가입 보너스",
        )
        updated_user, _ = await point_transaction_service.earn_by(
            user=test_user,
            amount=50,
            reason=TransactionReason.DIARY,
            reference_type=None,
            reference_id=None,
            description="일기 작성 보상",
        )

        # Then: 사용자의 current_points가 실제 거래 내역에서 계산한 잔액과 일치
        real_balance = await point_transaction_repository.calculate_real_balance_by_user_id(test_user.user_id)
        assert updated_user.current_points == real_balance
        assert updated_user.current_points.value == 1050


class TestPointTransactionServiceSpendBy:
    """PointTransactionService.spend_by() 메서드 테스트."""

    async def test_spend_by_success(
        self,
        point_transaction_service: PointTransactionService,
        test_user: User,
    ):
        """포인트를 정상적으로 차감할 수 있어야 합니다."""
        # Given: 1000 포인트를 적립
        await point_transaction_service.earn_by(
            user=test_user,
            amount=1000,
            reason=TransactionReason.SIGNED_UP,
            reference_type=TransactionReference.USERS,
            reference_id=test_user.user_id,
            description="회원가입 보너스",
        )

        # When: 300 포인트 차감
        updated_user, transaction = await point_transaction_service.spend_by(
            user=test_user,
            amount=300,
            reason=TransactionReason.TICKET,
            reference_type=TransactionReference.TICKETS,
            reference_id=Id(),
            description="일반 비행선 티켓 구매",
        )

        # Then: 사용자 잔액이 업데이트됨
        assert updated_user.current_points.value == 700
        # Then: 거래가 생성됨
        assert transaction.transaction_type == TransactionType.SPEND
        assert transaction.amount == 300
        assert transaction.balance_before.value == 1000
        assert transaction.balance_after.value == 700
        assert transaction.user_id == test_user.user_id

    async def test_spend_by_with_invalid_amount(
        self,
        point_transaction_service: PointTransactionService,
        test_user: User,
    ):
        """음수 금액으로 차감하려고 하면 에러가 발생해야 합니다."""
        # Given: 1000 포인트를 적립
        await point_transaction_service.earn_by(
            user=test_user,
            amount=1000,
            reason=TransactionReason.SIGNED_UP,
            reference_type=None,
            reference_id=None,
            description=None,
        )

        # When & Then: 음수 금액으로 차감 시도
        with pytest.raises(InvalidAmountError):
            await point_transaction_service.spend_by(
                user=test_user,
                amount=-100,
                reason=TransactionReason.TICKET,
                reference_type=None,
                reference_id=None,
                description=None,
            )

        # When & Then: 0 금액으로 차감 시도
        with pytest.raises(InvalidAmountError):
            await point_transaction_service.spend_by(
                user=test_user,
                amount=0,
                reason=TransactionReason.TICKET,
                reference_type=None,
                reference_id=None,
                description=None,
            )

    async def test_spend_by_with_insufficient_balance(
        self,
        point_transaction_service: PointTransactionService,
        test_user: User,
    ):
        """잔액이 부족하면 에러가 발생해야 합니다."""
        # Given: 100 포인트만 적립
        await point_transaction_service.earn_by(
            user=test_user,
            amount=100,
            reason=TransactionReason.SIGNED_UP,
            reference_type=None,
            reference_id=None,
            description=None,
        )

        # When & Then: 300 포인트를 차감하려고 하면 에러 발생
        with pytest.raises(InvalidAmountError):
            await point_transaction_service.spend_by(
                user=test_user,
                amount=300,
                reason=TransactionReason.TICKET,
                reference_type=None,
                reference_id=None,
                description=None,
            )

    async def test_spend_by_updates_user_balance_correctly(
        self,
        point_transaction_service: PointTransactionService,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        test_user: User,
    ):
        """차감 후 사용자 잔액이 실제 거래 내역과 일치해야 합니다."""
        # Given: 1000 포인트 적립
        await point_transaction_service.earn_by(
            user=test_user,
            amount=1000,
            reason=TransactionReason.SIGNED_UP,
            reference_type=None,
            reference_id=None,
            description=None,
        )

        # When: 여러 번 포인트 차감
        await point_transaction_service.spend_by(
            user=test_user,
            amount=300,
            reason=TransactionReason.TICKET,
            reference_type=None,
            reference_id=None,
            description="일반 비행선 티켓 구매",
        )
        updated_user, _ = await point_transaction_service.spend_by(
            user=test_user,
            amount=200,
            reason=TransactionReason.EXTENSION,
            reference_type=None,
            reference_id=None,
            description="숙박 연장",
        )

        # Then: 사용자의 current_points가 실제 거래 내역에서 계산한 잔액과 일치
        real_balance = await point_transaction_repository.calculate_real_balance_by_user_id(test_user.user_id)
        assert updated_user.current_points == real_balance
        assert updated_user.current_points.value == 500


class TestPointTransactionServiceIntegration:
    """PointTransactionService 통합 시나리오 테스트."""

    async def test_multiple_transactions_scenario(
        self,
        point_transaction_service: PointTransactionService,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        test_user: User,
    ):
        """여러 거래를 연속으로 실행해도 잔액이 정확해야 합니다."""
        # Scenario: 회원가입 → 일기 작성 → 티켓 구매 → 문답지 작성 → 숙박 연장

        # 1. 회원가입 보너스 (1000P)
        user, _ = await point_transaction_service.earn_by(
            user=test_user,
            amount=1000,
            reason=TransactionReason.SIGNED_UP,
            reference_type=TransactionReference.USERS,
            reference_id=test_user.user_id,
            description="회원가입 보너스",
        )
        assert user.current_points.value == 1000

        # 2. 일기 작성 보상 (50P)
        user, _ = await point_transaction_service.earn_by(
            user=user,
            amount=50,
            reason=TransactionReason.DIARY,
            reference_type=TransactionReference.DIARIES,
            reference_id=Id(),
            description="일기 작성 보상",
        )
        assert user.current_points.value == 1050

        # 3. 일반 비행선 티켓 구매 (300P)
        user, _ = await point_transaction_service.spend_by(
            user=user,
            amount=300,
            reason=TransactionReason.TICKET,
            reference_type=TransactionReference.TICKETS,
            reference_id=Id(),
            description="일반 비행선 티켓 구매",
        )
        assert user.current_points.value == 750

        # 4. 문답지 작성 보상 (50P)
        user, _ = await point_transaction_service.earn_by(
            user=user,
            amount=50,
            reason=TransactionReason.QUESTIONNAIRE,
            reference_type=None,
            reference_id=None,
            description="문답지 작성 보상",
        )
        assert user.current_points.value == 800

        # 5. 숙박 연장 (300P)
        user, _ = await point_transaction_service.spend_by(
            user=user,
            amount=300,
            reason=TransactionReason.EXTENSION,
            reference_type=None,
            reference_id=None,
            description="숙박 연장",
        )
        assert user.current_points.value == 500

        # 최종 검증: 실제 거래 내역에서 계산한 잔액과 일치
        real_balance = await point_transaction_repository.calculate_real_balance_by_user_id(test_user.user_id)
        assert user.current_points == real_balance
        assert user.current_points.value == 500

    async def test_balance_consistency_after_many_transactions(
        self,
        point_transaction_service: PointTransactionService,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        test_user: User,
    ):
        """많은 거래를 실행해도 잔액 일관성이 유지되어야 합니다."""
        # Given: 초기 잔액 0
        user = test_user
        expected_balance = 0

        # When: 10번의 적립과 5번의 차감
        for i in range(10):
            user, _ = await point_transaction_service.earn_by(
                user=user,
                amount=100,
                reason=TransactionReason.DIARY,
                reference_type=None,
                reference_id=None,
                description=f"일기 작성 보상 {i + 1}",
            )
            expected_balance += 100

        for i in range(5):
            user, _ = await point_transaction_service.spend_by(
                user=user,
                amount=50,
                reason=TransactionReason.TICKET,
                reference_type=None,
                reference_id=None,
                description=f"티켓 구매 {i + 1}",
            )
            expected_balance -= 50

        # Then: 최종 잔액이 정확함
        assert user.current_points.value == expected_balance
        assert expected_balance == 750

        # Then: 실제 거래 내역에서 계산한 잔액과 일치
        real_balance = await point_transaction_repository.calculate_real_balance_by_user_id(test_user.user_id)
        assert user.current_points == real_balance
