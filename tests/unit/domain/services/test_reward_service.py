from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest
from uuid_utils import uuid7

from bzero.domain.entities.reward import Reward
from bzero.domain.entities.user import User
from bzero.domain.errors import AlreadyClaimedRewardError, NotFoundUserError
from bzero.domain.repositories.reward import RewardRepository
from bzero.domain.repositories.user import UserRepository
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.services.reward import RewardService
from bzero.domain.value_objects import Balance, Id
from bzero.domain.value_objects.reward import RewardType


@pytest.fixture
def mock_reward_repository() -> MagicMock:
    """Mock RewardRepository"""
    return MagicMock(spec=RewardRepository)


@pytest.fixture
def mock_user_repository() -> MagicMock:
    """Mock UserRepository"""
    return MagicMock(spec=UserRepository)


@pytest.fixture
def mock_point_transaction_service() -> MagicMock:
    """Mock PointTransactionService"""
    return MagicMock(spec=PointTransactionService)


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone"""
    return ZoneInfo("Asia/Seoul")


@pytest.fixture
def reward_service(
    mock_reward_repository: MagicMock,
    mock_user_repository: MagicMock,
    mock_point_transaction_service: MagicMock,
    timezone: ZoneInfo,
) -> RewardService:
    """RewardService with mocked dependencies"""
    return RewardService(
        mock_reward_repository,
        mock_user_repository,
        mock_point_transaction_service,
        timezone,
    )


@pytest.fixture
def sample_user(timezone: ZoneInfo) -> User:
    """샘플 사용자"""
    now = datetime.now(timezone)
    return User(
        user_id=Id(uuid7()),
        email=None,
        nickname=None,
        profile=None,
        current_points=Balance(1000),
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_reward(timezone: ZoneInfo) -> Reward:
    """샘플 보상"""
    return Reward.create(
        user_id=Id(uuid7()),
        reward_type=RewardType.DAILY_LOGIN,
        amount=100,
        reference_date=datetime.now(timezone).date(),
    )


class TestRewardServiceClaimDailyLogin:
    """claim_daily_login 메서드 테스트"""

    async def test_claim_daily_login_success(
        self,
        reward_service: RewardService,
        mock_reward_repository: MagicMock,
        mock_user_repository: MagicMock,
        mock_point_transaction_service: MagicMock,
        sample_user: User,
        timezone: ZoneInfo,
    ):
        """일일 출석 보상을 성공적으로 수령할 수 있다"""
        # Given
        user_id = sample_user.user_id
        mock_reward_repository.find_by_user_type_date = AsyncMock(return_value=None)
        mock_user_repository.find_by_user_id = AsyncMock(return_value=sample_user)

        mock_point_tx = MagicMock()
        mock_point_tx.point_transaction_id = Id(uuid7())
        mock_point_transaction_service.earn_by = AsyncMock(return_value=(sample_user, mock_point_tx))

        async def mock_create(reward: Reward) -> Reward:
            return reward

        mock_reward_repository.create = AsyncMock(side_effect=mock_create)

        # When
        reward = await reward_service.claim_daily_login(user_id)

        # Then
        assert reward.user_id == user_id
        assert reward.reward_type == RewardType.DAILY_LOGIN
        assert reward.amount == 100
        assert reward.reference_date == datetime.now(timezone).date()
        assert reward.point_transaction_id == mock_point_tx.point_transaction_id

        mock_reward_repository.find_by_user_type_date.assert_called_once()
        mock_user_repository.find_by_user_id.assert_called_once_with(user_id)
        mock_point_transaction_service.earn_by.assert_called_once()
        mock_reward_repository.create.assert_called_once()

    async def test_claim_daily_login_raises_error_when_already_claimed(
        self,
        reward_service: RewardService,
        mock_reward_repository: MagicMock,
        sample_reward: Reward,
    ):
        """이미 오늘 보상을 받았으면 에러가 발생한다"""
        # Given
        user_id = sample_reward.user_id
        mock_reward_repository.find_by_user_type_date = AsyncMock(return_value=sample_reward)

        # When/Then
        with pytest.raises(AlreadyClaimedRewardError):
            await reward_service.claim_daily_login(user_id)

        mock_reward_repository.find_by_user_type_date.assert_called_once()

    async def test_claim_daily_login_raises_error_when_user_not_found(
        self,
        reward_service: RewardService,
        mock_reward_repository: MagicMock,
        mock_user_repository: MagicMock,
    ):
        """사용자를 찾을 수 없으면 에러가 발생한다"""
        # Given
        user_id = Id(uuid7())
        mock_reward_repository.find_by_user_type_date = AsyncMock(return_value=None)
        mock_user_repository.find_by_user_id = AsyncMock(return_value=None)

        # When/Then
        with pytest.raises(NotFoundUserError):
            await reward_service.claim_daily_login(user_id)


class TestRewardServiceGetTodayReward:
    """get_today_reward 메서드 테스트"""

    async def test_get_today_reward_success(
        self,
        reward_service: RewardService,
        mock_reward_repository: MagicMock,
        sample_reward: Reward,
    ):
        """오늘 보상을 조회할 수 있다"""
        # Given
        user_id = sample_reward.user_id
        mock_reward_repository.find_by_user_type_date = AsyncMock(return_value=sample_reward)

        # When
        reward = await reward_service.get_today_reward(user_id, RewardType.DAILY_LOGIN)

        # Then
        assert reward is not None
        assert reward.user_id == user_id
        assert reward.reward_type == RewardType.DAILY_LOGIN
        mock_reward_repository.find_by_user_type_date.assert_called_once()

    async def test_get_today_reward_returns_none_when_not_found(
        self,
        reward_service: RewardService,
        mock_reward_repository: MagicMock,
    ):
        """보상이 없으면 None을 반환한다"""
        # Given
        user_id = Id(uuid7())
        mock_reward_repository.find_by_user_type_date = AsyncMock(return_value=None)

        # When
        reward = await reward_service.get_today_reward(user_id, RewardType.DAILY_LOGIN)

        # Then
        assert reward is None
