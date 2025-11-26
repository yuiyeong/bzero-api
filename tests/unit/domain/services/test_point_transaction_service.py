"""PointTransactionService 단위 테스트"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from bzero.domain.entities.user import User
from bzero.domain.errors import DuplicatedRewardError, InvalidAmountError
from bzero.domain.repositories.point_transaction import PointTransactionRepository
from bzero.domain.repositories.user import UserRepository
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.value_objects import Balance, Email, Id, TransactionReason, TransactionReference


@pytest.fixture
def mock_user_repository() -> MagicMock:
    """Mock UserRepository"""
    return MagicMock(spec=UserRepository)


@pytest.fixture
def mock_point_transaction_repository() -> MagicMock:
    """Mock PointTransactionRepository"""
    return MagicMock(spec=PointTransactionRepository)


@pytest.fixture
def point_transaction_service(
    mock_user_repository: MagicMock,
    mock_point_transaction_repository: MagicMock,
) -> PointTransactionService:
    """PointTransactionService with mocked repositories"""
    return PointTransactionService(mock_user_repository, mock_point_transaction_repository)


@pytest.fixture
def sample_user() -> User:
    """테스트용 User"""
    return User(
        user_id=Id(),
        email=Email("test@example.com"),
        nickname=None,
        profile=None,
        current_points=Balance(0),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestPointTransactionServiceEarnBy:
    """earn_by 메서드 테스트"""

    async def test_earn_by_success(
        self,
        point_transaction_service: PointTransactionService,
        mock_user_repository: MagicMock,
        mock_point_transaction_repository: MagicMock,
        sample_user: User,
    ):
        """포인트를 성공적으로 적립한다"""
        # Given
        amount = 1000
        reason = TransactionReason.SIGNED_UP
        reference_type = TransactionReference.USERS
        reference_id = sample_user.user_id

        mock_point_transaction_repository.exists_by_reference = AsyncMock(return_value=False)
        mock_point_transaction_repository.calculate_real_balance_by_user_id = AsyncMock(return_value=Balance(0))
        mock_point_transaction_repository.create = AsyncMock(side_effect=lambda tx: tx)

        updated_user = User(
            user_id=sample_user.user_id,
            email=sample_user.email,
            nickname=None,
            profile=None,
            current_points=Balance(amount),
            created_at=sample_user.created_at,
            updated_at=datetime.now(),
        )
        mock_user_repository.update = AsyncMock(return_value=updated_user)

        # When
        result_user, result_tx = await point_transaction_service.earn_by(
            user=sample_user,
            amount=amount,
            reason=reason,
            reference_type=reference_type,
            reference_id=reference_id,
            description="회원가입 보너스",
        )

        # Then
        assert result_user.current_points.value == amount
        assert result_tx.amount == amount
        assert result_tx.balance_before.value == 0
        assert result_tx.balance_after.value == amount

        mock_point_transaction_repository.exists_by_reference.assert_called_once_with(reference_type, reference_id)
        mock_point_transaction_repository.create.assert_called_once()
        mock_user_repository.update.assert_called_once()

    async def test_earn_by_adds_to_existing_balance(
        self,
        point_transaction_service: PointTransactionService,
        mock_user_repository: MagicMock,
        mock_point_transaction_repository: MagicMock,
        sample_user: User,
    ):
        """기존 잔액에 포인트를 더한다"""
        # Given
        existing_balance = 500
        earn_amount = 100

        mock_point_transaction_repository.exists_by_reference = AsyncMock(return_value=False)
        mock_point_transaction_repository.calculate_real_balance_by_user_id = AsyncMock(
            return_value=Balance(existing_balance)
        )
        mock_point_transaction_repository.create = AsyncMock(side_effect=lambda tx: tx)

        updated_user = User(
            user_id=sample_user.user_id,
            email=sample_user.email,
            nickname=None,
            profile=None,
            current_points=Balance(existing_balance + earn_amount),
            created_at=sample_user.created_at,
            updated_at=datetime.now(),
        )
        mock_user_repository.update = AsyncMock(return_value=updated_user)

        # When
        _, result_tx = await point_transaction_service.earn_by(
            user=sample_user,
            amount=earn_amount,
            reason=TransactionReason.DIARY,
            reference_type=None,
            reference_id=None,
        )

        # Then
        assert result_tx.balance_before.value == existing_balance
        assert result_tx.balance_after.value == existing_balance + earn_amount

    async def test_earn_by_raises_invalid_amount_error_when_amount_is_zero(
        self,
        point_transaction_service: PointTransactionService,
        sample_user: User,
    ):
        """amount가 0이면 InvalidAmountError를 발생시킨다"""
        # When & Then
        with pytest.raises(InvalidAmountError):
            await point_transaction_service.earn_by(
                user=sample_user,
                amount=0,
                reason=TransactionReason.DIARY,
                reference_type=None,
                reference_id=None,
            )

    async def test_earn_by_raises_invalid_amount_error_when_amount_is_negative(
        self,
        point_transaction_service: PointTransactionService,
        sample_user: User,
    ):
        """amount가 음수면 InvalidAmountError를 발생시킨다"""
        # When & Then
        with pytest.raises(InvalidAmountError):
            await point_transaction_service.earn_by(
                user=sample_user,
                amount=-100,
                reason=TransactionReason.DIARY,
                reference_type=None,
                reference_id=None,
            )

    async def test_earn_by_raises_duplicated_reward_error(
        self,
        point_transaction_service: PointTransactionService,
        mock_point_transaction_repository: MagicMock,
        sample_user: User,
    ):
        """중복 지급 시도 시 DuplicatedRewardError를 발생시킨다"""
        # Given
        reference_type = TransactionReference.USERS
        reference_id = sample_user.user_id

        mock_point_transaction_repository.exists_by_reference = AsyncMock(return_value=True)

        # When & Then
        with pytest.raises(DuplicatedRewardError):
            await point_transaction_service.earn_by(
                user=sample_user,
                amount=1000,
                reason=TransactionReason.SIGNED_UP,
                reference_type=reference_type,
                reference_id=reference_id,
            )

        mock_point_transaction_repository.exists_by_reference.assert_called_once_with(reference_type, reference_id)

    async def test_earn_by_skips_duplicate_check_when_no_reference(
        self,
        point_transaction_service: PointTransactionService,
        mock_user_repository: MagicMock,
        mock_point_transaction_repository: MagicMock,
        sample_user: User,
    ):
        """reference가 없으면 중복 체크를 건너뛴다"""
        # Given
        mock_point_transaction_repository.calculate_real_balance_by_user_id = AsyncMock(return_value=Balance(0))
        mock_point_transaction_repository.create = AsyncMock(side_effect=lambda tx: tx)
        mock_user_repository.update = AsyncMock(side_effect=lambda user: user)

        # When
        await point_transaction_service.earn_by(
            user=sample_user,
            amount=50,
            reason=TransactionReason.DIARY,
            reference_type=None,
            reference_id=None,
        )

        # Then
        mock_point_transaction_repository.exists_by_reference.assert_not_called()


class TestPointTransactionServiceSpendBy:
    """spend_by 메서드 테스트"""

    async def test_spend_by_success(
        self,
        point_transaction_service: PointTransactionService,
        mock_user_repository: MagicMock,
        mock_point_transaction_repository: MagicMock,
        sample_user: User,
    ):
        """포인트를 성공적으로 차감한다"""
        # Given
        existing_balance = 1000
        spend_amount = 300

        mock_point_transaction_repository.calculate_real_balance_by_user_id = AsyncMock(
            return_value=Balance(existing_balance)
        )
        mock_point_transaction_repository.create = AsyncMock(side_effect=lambda tx: tx)

        updated_user = User(
            user_id=sample_user.user_id,
            email=sample_user.email,
            nickname=None,
            profile=None,
            current_points=Balance(existing_balance - spend_amount),
            created_at=sample_user.created_at,
            updated_at=datetime.now(),
        )
        mock_user_repository.update = AsyncMock(return_value=updated_user)

        # When
        result_user, result_tx = await point_transaction_service.spend_by(
            user=sample_user,
            amount=spend_amount,
            reason=TransactionReason.TICKET,
            reference_type=TransactionReference.TICKETS,
            reference_id=Id(),
            description="비행선 티켓 구매",
        )

        # Then
        assert result_user.current_points.value == existing_balance - spend_amount
        assert result_tx.amount == spend_amount
        assert result_tx.balance_before.value == existing_balance
        assert result_tx.balance_after.value == existing_balance - spend_amount

    async def test_spend_by_raises_invalid_amount_error_when_amount_is_zero(
        self,
        point_transaction_service: PointTransactionService,
        sample_user: User,
    ):
        """amount가 0이면 InvalidAmountError를 발생시킨다"""
        # When & Then
        with pytest.raises(InvalidAmountError):
            await point_transaction_service.spend_by(
                user=sample_user,
                amount=0,
                reason=TransactionReason.TICKET,
                reference_type=None,
                reference_id=None,
            )

    async def test_spend_by_raises_invalid_amount_error_when_amount_is_negative(
        self,
        point_transaction_service: PointTransactionService,
        sample_user: User,
    ):
        """amount가 음수면 InvalidAmountError를 발생시킨다"""
        # When & Then
        with pytest.raises(InvalidAmountError):
            await point_transaction_service.spend_by(
                user=sample_user,
                amount=-100,
                reason=TransactionReason.TICKET,
                reference_type=None,
                reference_id=None,
            )

    async def test_spend_by_raises_invalid_amount_error_when_insufficient_balance(
        self,
        point_transaction_service: PointTransactionService,
        mock_point_transaction_repository: MagicMock,
        sample_user: User,
    ):
        """잔액이 부족하면 InvalidAmountError를 발생시킨다"""
        # Given
        existing_balance = 100
        spend_amount = 500

        mock_point_transaction_repository.calculate_real_balance_by_user_id = AsyncMock(
            return_value=Balance(existing_balance)
        )

        # When & Then
        with pytest.raises(InvalidAmountError):
            await point_transaction_service.spend_by(
                user=sample_user,
                amount=spend_amount,
                reason=TransactionReason.TICKET,
                reference_type=None,
                reference_id=None,
            )

    async def test_spend_by_allows_spending_entire_balance(
        self,
        point_transaction_service: PointTransactionService,
        mock_user_repository: MagicMock,
        mock_point_transaction_repository: MagicMock,
        sample_user: User,
    ):
        """전체 잔액을 사용할 수 있다"""
        # Given
        existing_balance = 300
        spend_amount = 300

        mock_point_transaction_repository.calculate_real_balance_by_user_id = AsyncMock(
            return_value=Balance(existing_balance)
        )
        mock_point_transaction_repository.create = AsyncMock(side_effect=lambda tx: tx)

        updated_user = User(
            user_id=sample_user.user_id,
            email=sample_user.email,
            nickname=None,
            profile=None,
            current_points=Balance(0),
            created_at=sample_user.created_at,
            updated_at=datetime.now(),
        )
        mock_user_repository.update = AsyncMock(return_value=updated_user)

        # When
        _, result_tx = await point_transaction_service.spend_by(
            user=sample_user,
            amount=spend_amount,
            reason=TransactionReason.TICKET,
            reference_type=None,
            reference_id=None,
        )

        # Then
        assert result_tx.balance_after.value == 0
