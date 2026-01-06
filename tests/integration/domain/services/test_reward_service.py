"""RewardService 통합 테스트"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.errors import AlreadyClaimedRewardError, NotFoundUserError
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.services.reward import RewardService
from bzero.domain.value_objects import Id, TransactionStatus, TransactionType
from bzero.domain.value_objects.point_transaction import TransactionReason, TransactionReference
from bzero.domain.value_objects.reward import RewardType
from bzero.infrastructure.db.point_transaction_model import PointTransactionModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.point_transaction import SqlAlchemyPointTransactionRepository
from bzero.infrastructure.repositories.reward import SqlAlchemyRewardRepository
from bzero.infrastructure.repositories.user import SqlAlchemyUserRepository


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone"""
    return get_settings().timezone


@pytest.fixture
def reward_service(test_session: AsyncSession, timezone: ZoneInfo) -> RewardService:
    """RewardService fixture를 생성합니다."""
    reward_repo = SqlAlchemyRewardRepository(test_session)
    user_repo = SqlAlchemyUserRepository(test_session)
    point_tx_repo = SqlAlchemyPointTransactionRepository(test_session)
    point_tx_service = PointTransactionService(user_repo, point_tx_repo)
    return RewardService(reward_repo, user_repo, point_tx_service, timezone)


@pytest.fixture
async def sample_user(test_session: AsyncSession, timezone: ZoneInfo) -> UserModel:
    """테스트용 샘플 유저 데이터를 생성합니다.

    초기 포인트 1000P에 대한 PointTransaction도 함께 생성합니다.
    """
    now = datetime.now(timezone)
    user_id = uuid7()

    user = UserModel(
        user_id=user_id,
        email="reward_service_test@example.com",
        nickname="보상서비스테스트",
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


# =============================================================================
# Tests: claim_daily_login
# =============================================================================


class TestRewardServiceClaimDailyLogin:
    """claim_daily_login 메서드 통합 테스트"""

    async def test_claim_daily_login_success(
        self,
        reward_service: RewardService,
        sample_user: UserModel,
        timezone: ZoneInfo,
    ):
        """일일 출석 보상을 성공적으로 수령할 수 있다"""
        # Given
        user_id = Id(sample_user.user_id)
        today = datetime.now(timezone).date()

        # When
        reward = await reward_service.claim_daily_login(user_id)

        # Then
        assert reward.user_id == user_id
        assert reward.reward_type == RewardType.DAILY_LOGIN
        assert reward.amount == 100
        assert reward.reference_date == today
        assert reward.point_transaction_id is not None

    async def test_claim_daily_login_increases_user_points(
        self,
        test_session: AsyncSession,
        reward_service: RewardService,
        sample_user: UserModel,
    ):
        """일일 출석 보상 수령 시 사용자 포인트가 증가한다"""
        # Given
        user_id = Id(sample_user.user_id)
        initial_points = sample_user.current_points

        # When
        await reward_service.claim_daily_login(user_id)
        await test_session.flush()
        await test_session.refresh(sample_user)

        # Then
        assert sample_user.current_points == initial_points + 100

    async def test_claim_daily_login_raises_error_when_already_claimed(
        self,
        reward_service: RewardService,
        sample_user: UserModel,
    ):
        """이미 오늘 보상을 받았으면 에러가 발생한다"""
        # Given
        user_id = Id(sample_user.user_id)

        # 첫 번째 수령
        await reward_service.claim_daily_login(user_id)

        # When/Then - 두 번째 수령 시도
        with pytest.raises(AlreadyClaimedRewardError):
            await reward_service.claim_daily_login(user_id)

    async def test_claim_daily_login_raises_error_when_user_not_found(
        self,
        reward_service: RewardService,
    ):
        """사용자를 찾을 수 없으면 에러가 발생한다"""
        # Given
        non_existent_user_id = Id(uuid7())

        # When/Then
        with pytest.raises(NotFoundUserError):
            await reward_service.claim_daily_login(non_existent_user_id)


# =============================================================================
# Tests: get_today_reward
# =============================================================================


class TestRewardServiceGetTodayReward:
    """get_today_reward 메서드 통합 테스트"""

    async def test_get_today_reward_returns_reward_when_exists(
        self,
        reward_service: RewardService,
        sample_user: UserModel,
    ):
        """오늘 보상이 있으면 해당 보상을 반환한다"""
        # Given
        user_id = Id(sample_user.user_id)
        await reward_service.claim_daily_login(user_id)

        # When
        reward = await reward_service.get_today_reward(user_id, RewardType.DAILY_LOGIN)

        # Then
        assert reward is not None
        assert reward.user_id == user_id
        assert reward.reward_type == RewardType.DAILY_LOGIN

    async def test_get_today_reward_returns_none_when_not_claimed(
        self,
        reward_service: RewardService,
        sample_user: UserModel,
    ):
        """오늘 보상을 받지 않았으면 None을 반환한다"""
        # Given
        user_id = Id(sample_user.user_id)

        # When
        reward = await reward_service.get_today_reward(user_id, RewardType.DAILY_LOGIN)

        # Then
        assert reward is None


# =============================================================================
# Tests: KST Date Boundary
# =============================================================================


class TestRewardServiceKSTDateBoundary:
    """KST 날짜 경계 테스트"""

    async def test_reward_uses_kst_date(
        self,
        reward_service: RewardService,
        sample_user: UserModel,
        timezone: ZoneInfo,
    ):
        """보상은 KST 기준 날짜를 사용한다"""
        # Given
        user_id = Id(sample_user.user_id)
        today_kst = datetime.now(timezone).date()

        # When
        reward = await reward_service.claim_daily_login(user_id)

        # Then
        assert reward.reference_date == today_kst
