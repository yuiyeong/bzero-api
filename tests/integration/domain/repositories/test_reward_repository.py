"""RewardRepository 통합 테스트"""

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.domain.entities.reward import Reward
from bzero.domain.value_objects.common import Id
from bzero.domain.value_objects.reward import RewardType
from bzero.infrastructure.db.point_transaction_model import PointTransactionModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.reward import SqlAlchemyRewardRepository


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def reward_repository(test_session: AsyncSession) -> SqlAlchemyRewardRepository:
    """RewardRepository fixture를 생성합니다."""
    return SqlAlchemyRewardRepository(test_session)


@pytest.fixture
async def sample_user(test_session: AsyncSession) -> UserModel:
    """테스트용 샘플 유저 데이터를 생성합니다."""
    now = datetime.now()
    user = UserModel(
        user_id=uuid7(),
        email="reward_test@example.com",
        nickname="보상테스트",
        profile_emoji="🌟",
        current_points=1000,
        created_at=now,
        updated_at=now,
    )
    test_session.add(user)
    await test_session.flush()
    return user


@pytest.fixture
async def sample_point_transaction(test_session: AsyncSession, sample_user: UserModel) -> PointTransactionModel:
    """테스트용 샘플 포인트 트랜잭션을 생성합니다."""
    now = datetime.now()
    point_tx = PointTransactionModel(
        point_transaction_id=uuid7(),
        user_id=sample_user.user_id,
        transaction_type="earn",
        amount=100,
        reason="daily_login",
        status="completed",
        balance_before=1000,
        balance_after=1100,
        created_at=now,
        updated_at=now,
    )
    test_session.add(point_tx)
    await test_session.flush()
    return point_tx


# =============================================================================
# Tests: create
# =============================================================================


class TestRewardRepositoryCreate:
    """create 메서드 테스트"""

    async def test_create_reward_success(
        self,
        reward_repository: SqlAlchemyRewardRepository,
        sample_user: UserModel,
    ):
        """보상을 생성할 수 있다"""
        # Given
        user_id = Id(sample_user.user_id)
        today = date.today()
        reward = Reward.create(
            user_id=user_id,
            reward_type=RewardType.DAILY_LOGIN,
            amount=100,
            reference_date=today,
        )

        # When
        created_reward = await reward_repository.create(reward)

        # Then
        assert created_reward.reward_id == reward.reward_id
        assert created_reward.user_id == user_id
        assert created_reward.reward_type == RewardType.DAILY_LOGIN
        assert created_reward.amount == 100
        assert created_reward.reference_date == today

    async def test_create_reward_with_point_transaction(
        self,
        reward_repository: SqlAlchemyRewardRepository,
        sample_user: UserModel,
        sample_point_transaction: PointTransactionModel,
    ):
        """포인트 트랜잭션과 연결된 보상을 생성할 수 있다"""
        # Given
        user_id = Id(sample_user.user_id)
        point_tx_id = Id(sample_point_transaction.point_transaction_id)
        today = date.today()

        reward = Reward.create(
            user_id=user_id,
            reward_type=RewardType.DAILY_LOGIN,
            amount=100,
            reference_date=today,
        )
        reward.point_transaction_id = point_tx_id

        # When
        created_reward = await reward_repository.create(reward)

        # Then
        assert created_reward.point_transaction_id == point_tx_id


# =============================================================================
# Tests: exists_by_user_type_date
# =============================================================================


class TestRewardRepositoryExistsByUserTypeDate:
    """exists_by_user_type_date 메서드 테스트"""

    async def test_exists_returns_true_when_reward_exists(
        self,
        reward_repository: SqlAlchemyRewardRepository,
        sample_user: UserModel,
    ):
        """보상이 존재하면 True를 반환한다"""
        # Given
        user_id = Id(sample_user.user_id)
        today = date.today()
        reward = Reward.create(
            user_id=user_id,
            reward_type=RewardType.DAILY_LOGIN,
            amount=100,
            reference_date=today,
        )
        await reward_repository.create(reward)

        # When
        exists = await reward_repository.exists_by_user_type_date(user_id, RewardType.DAILY_LOGIN, today)

        # Then
        assert exists is True

    async def test_exists_returns_false_when_reward_not_exists(
        self,
        reward_repository: SqlAlchemyRewardRepository,
        sample_user: UserModel,
    ):
        """보상이 존재하지 않으면 False를 반환한다"""
        # Given
        user_id = Id(sample_user.user_id)
        today = date.today()

        # When
        exists = await reward_repository.exists_by_user_type_date(user_id, RewardType.DAILY_LOGIN, today)

        # Then
        assert exists is False

    async def test_exists_returns_false_for_different_date(
        self,
        reward_repository: SqlAlchemyRewardRepository,
        sample_user: UserModel,
    ):
        """다른 날짜의 보상은 False를 반환한다"""
        # Given
        user_id = Id(sample_user.user_id)
        today = date.today()
        yesterday = today - timedelta(days=1)

        reward = Reward.create(
            user_id=user_id,
            reward_type=RewardType.DAILY_LOGIN,
            amount=100,
            reference_date=yesterday,
        )
        await reward_repository.create(reward)

        # When
        exists = await reward_repository.exists_by_user_type_date(user_id, RewardType.DAILY_LOGIN, today)

        # Then
        assert exists is False


# =============================================================================
# Tests: find_by_user_type_date
# =============================================================================


class TestRewardRepositoryFindByUserTypeDate:
    """find_by_user_type_date 메서드 테스트"""

    async def test_find_returns_reward_when_exists(
        self,
        reward_repository: SqlAlchemyRewardRepository,
        sample_user: UserModel,
    ):
        """보상이 존재하면 해당 보상을 반환한다"""
        # Given
        user_id = Id(sample_user.user_id)
        today = date.today()
        reward = Reward.create(
            user_id=user_id,
            reward_type=RewardType.DAILY_LOGIN,
            amount=100,
            reference_date=today,
        )
        await reward_repository.create(reward)

        # When
        found_reward = await reward_repository.find_by_user_type_date(user_id, RewardType.DAILY_LOGIN, today)

        # Then
        assert found_reward is not None
        assert found_reward.reward_id == reward.reward_id
        assert found_reward.user_id == user_id
        assert found_reward.reward_type == RewardType.DAILY_LOGIN
        assert found_reward.amount == 100

    async def test_find_returns_none_when_not_exists(
        self,
        reward_repository: SqlAlchemyRewardRepository,
        sample_user: UserModel,
    ):
        """보상이 존재하지 않으면 None을 반환한다"""
        # Given
        user_id = Id(sample_user.user_id)
        today = date.today()

        # When
        found_reward = await reward_repository.find_by_user_type_date(user_id, RewardType.DAILY_LOGIN, today)

        # Then
        assert found_reward is None


# =============================================================================
# Tests: UNIQUE constraint
# =============================================================================


class TestRewardRepositoryUniqueConstraint:
    """UNIQUE 제약조건 테스트"""

    async def test_duplicate_reward_raises_integrity_error(
        self,
        test_session: AsyncSession,
        reward_repository: SqlAlchemyRewardRepository,
        sample_user: UserModel,
    ):
        """같은 사용자가 같은 날 같은 유형의 보상을 중복으로 받으면 에러가 발생한다"""
        # Given
        user_id = Id(sample_user.user_id)
        today = date.today()

        reward1 = Reward.create(
            user_id=user_id,
            reward_type=RewardType.DAILY_LOGIN,
            amount=100,
            reference_date=today,
        )
        await reward_repository.create(reward1)
        await test_session.flush()

        reward2 = Reward.create(
            user_id=user_id,
            reward_type=RewardType.DAILY_LOGIN,
            amount=100,
            reference_date=today,
        )

        # When/Then - create 시점에 IntegrityError 발생
        with pytest.raises(IntegrityError):
            await reward_repository.create(reward2)
