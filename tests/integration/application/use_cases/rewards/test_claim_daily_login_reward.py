"""ClaimDailyLoginRewardUseCase 통합 테스트"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.application.use_cases.rewards.claim_daily_login_reward import ClaimDailyLoginRewardUseCase
from bzero.core.settings import get_settings
from bzero.domain.errors import NotFoundUserError
from bzero.domain.value_objects import AuthProvider, Id, TransactionStatus, TransactionType
from bzero.domain.value_objects.point_transaction import TransactionReason, TransactionReference
from bzero.domain.value_objects.reward import RewardType
from bzero.infrastructure.db.point_transaction_model import PointTransactionModel
from bzero.infrastructure.db.user_identity_model import UserIdentityModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.point_transaction import SqlAlchemyPointTransactionRepository
from bzero.infrastructure.repositories.user import SqlAlchemyUserRepository


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone"""
    return get_settings().timezone


@pytest.fixture
def use_case(test_session: AsyncSession, timezone: ZoneInfo) -> ClaimDailyLoginRewardUseCase:
    """ClaimDailyLoginRewardUseCase fixture를 생성합니다."""
    return ClaimDailyLoginRewardUseCase(test_session, timezone)


@pytest_asyncio.fixture
async def sample_user(test_session: AsyncSession, timezone: ZoneInfo) -> UserModel:
    """테스트용 샘플 유저 데이터를 생성합니다.

    초기 포인트 1000P에 대한 PointTransaction도 함께 생성합니다.
    """
    now = datetime.now(timezone)
    user_id = uuid7()

    user = UserModel(
        user_id=user_id,
        email="reward_usecase_test@example.com",
        nickname="보상유즈케이스테스트",
        profile_emoji="🌟",
        current_points=1000,
        created_at=now,
        updated_at=now,
    )
    test_session.add(user)
    await test_session.flush()

    # 초기 포인트에 대한 PointTransaction 생성
    initial_point_tx = PointTransactionModel(
        point_transaction_id=uuid7(),
        user_id=user_id,
        transaction_type=TransactionType.EARN.value,
        amount=1000,
        reason=TransactionReason.SIGNED_UP.value,
        status=TransactionStatus.COMPLETED.value,
        reference_type=TransactionReference.USERS.value,
        reference_id=user_id,
        balance_before=0,
        balance_after=1000,
        description="회원가입 보너스",
        created_at=now,
        updated_at=now,
    )
    test_session.add(initial_point_tx)
    await test_session.flush()

    return user


@pytest_asyncio.fixture
async def sample_user_identity(
    test_session: AsyncSession,
    sample_user: UserModel,
    timezone: ZoneInfo,
) -> UserIdentityModel:
    """테스트용 사용자 인증 정보를 생성합니다."""
    now = datetime.now(timezone)
    identity = UserIdentityModel(
        identity_id=uuid7(),
        user_id=sample_user.user_id,
        provider=AuthProvider.EMAIL.value,
        provider_user_id="test-reward-provider-user-123",
        created_at=now,
        updated_at=now,
    )
    test_session.add(identity)
    await test_session.flush()
    return identity


# =============================================================================
# Tests: ClaimDailyLoginRewardUseCase
# =============================================================================


class TestClaimDailyLoginRewardUseCase:
    """ClaimDailyLoginRewardUseCase 통합 테스트"""

    async def test_first_claim_returns_claimed_true(
        self,
        use_case: ClaimDailyLoginRewardUseCase,
        sample_user_identity: UserIdentityModel,
        sample_user: UserModel,
        timezone: ZoneInfo,
    ):
        """첫 번째 보상 수령 시 claimed=True와 보상 정보를 반환한다"""
        # Given
        today = datetime.now(timezone).date()

        # When
        result = await use_case.execute(
            provider=sample_user_identity.provider,
            provider_user_id=sample_user_identity.provider_user_id,
        )

        # Then
        assert result.claimed is True
        assert result.reward_type == RewardType.DAILY_LOGIN.value
        assert result.amount == 100
        assert result.reference_date == today.isoformat()
        assert result.point_transaction_id is not None

    async def test_second_claim_same_day_returns_claimed_false(
        self,
        use_case: ClaimDailyLoginRewardUseCase,
        sample_user_identity: UserIdentityModel,
    ):
        """같은 날 두 번째 보상 수령 시 claimed=False와 기존 보상 정보를 반환한다"""
        # Given - 첫 번째 수령
        first_result = await use_case.execute(
            provider=sample_user_identity.provider,
            provider_user_id=sample_user_identity.provider_user_id,
        )

        # When - 두 번째 수령 시도
        second_result = await use_case.execute(
            provider=sample_user_identity.provider,
            provider_user_id=sample_user_identity.provider_user_id,
        )

        # Then
        assert second_result.claimed is False
        assert second_result.reward_id == first_result.reward_id
        assert second_result.amount == 100

    async def test_claim_increases_user_points(
        self,
        test_session: AsyncSession,
        use_case: ClaimDailyLoginRewardUseCase,
        sample_user_identity: UserIdentityModel,
        sample_user: UserModel,
    ):
        """보상 수령 시 사용자 포인트가 증가한다"""
        # Given
        initial_points = sample_user.current_points
        user_repo = SqlAlchemyUserRepository(test_session)

        # When
        await use_case.execute(
            provider=sample_user_identity.provider,
            provider_user_id=sample_user_identity.provider_user_id,
        )

        # Then
        updated_user = await user_repo.find_by_user_id(Id(sample_user.user_id))
        assert updated_user is not None
        assert updated_user.current_points.value == initial_points + 100

    async def test_second_claim_does_not_increase_points(
        self,
        test_session: AsyncSession,
        use_case: ClaimDailyLoginRewardUseCase,
        sample_user_identity: UserIdentityModel,
        sample_user: UserModel,
    ):
        """두 번째 수령 시도 시 포인트가 증가하지 않는다"""
        # Given - 첫 번째 수령
        await use_case.execute(
            provider=sample_user_identity.provider,
            provider_user_id=sample_user_identity.provider_user_id,
        )
        user_repo = SqlAlchemyUserRepository(test_session)
        user_after_first = await user_repo.find_by_user_id(Id(sample_user.user_id))
        points_after_first = user_after_first.current_points.value

        # When - 두 번째 수령 시도
        await use_case.execute(
            provider=sample_user_identity.provider,
            provider_user_id=sample_user_identity.provider_user_id,
        )

        # Then
        user_after_second = await user_repo.find_by_user_id(Id(sample_user.user_id))
        assert user_after_second.current_points.value == points_after_first

    async def test_claim_creates_point_transaction(
        self,
        test_session: AsyncSession,
        use_case: ClaimDailyLoginRewardUseCase,
        sample_user_identity: UserIdentityModel,
        sample_user: UserModel,
    ):
        """보상 수령 시 포인트 트랜잭션이 생성된다"""
        # Given
        point_tx_repo = SqlAlchemyPointTransactionRepository(test_session)

        # When
        result = await use_case.execute(
            provider=sample_user_identity.provider,
            provider_user_id=sample_user_identity.provider_user_id,
        )

        # Then
        point_tx = await point_tx_repo.find_by_id(Id.from_hex(result.point_transaction_id))
        assert point_tx is not None
        assert point_tx.amount == 100
        assert point_tx.transaction_type == TransactionType.EARN

    async def test_claim_with_nonexistent_user_raises_error(
        self,
        use_case: ClaimDailyLoginRewardUseCase,
    ):
        """존재하지 않는 사용자로 보상 수령 시 에러가 발생한다"""
        # Given
        non_existent_provider_user_id = "non-existent-provider-user-id"

        # When/Then
        with pytest.raises(NotFoundUserError):
            await use_case.execute(
                provider=AuthProvider.EMAIL.value,
                provider_user_id=non_existent_provider_user_id,
            )

    async def test_idempotent_response_structure(
        self,
        use_case: ClaimDailyLoginRewardUseCase,
        sample_user_identity: UserIdentityModel,
    ):
        """멱등성: 여러 번 호출해도 응답 구조가 동일하다"""
        # Given/When - 세 번 연속 호출
        results = []
        for _ in range(3):
            result = await use_case.execute(
                provider=sample_user_identity.provider,
                provider_user_id=sample_user_identity.provider_user_id,
            )
            results.append(result)

        # Then - 첫 번째만 claimed=True, 나머지는 False
        assert results[0].claimed is True
        assert results[1].claimed is False
        assert results[2].claimed is False

        # Then - 모두 같은 reward_id를 반환
        assert results[0].reward_id == results[1].reward_id == results[2].reward_id
