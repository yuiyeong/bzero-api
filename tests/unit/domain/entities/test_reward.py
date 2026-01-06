from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.entities.reward import Reward
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.reward import RewardType


class TestReward:
    """Reward 엔티티 단위 테스트"""

    @pytest.fixture
    def tz(self) -> ZoneInfo:
        """Seoul timezone"""
        return get_settings().timezone

    def test_create_reward(self, tz: ZoneInfo):
        """보상을 생성할 수 있다"""
        # Given
        user_id = Id(uuid7())
        reward_type = RewardType.DAILY_LOGIN
        amount = 100
        reference_date = datetime.now(tz).date()

        # When
        reward = Reward.create(
            user_id=user_id,
            reward_type=reward_type,
            amount=amount,
            reference_date=reference_date,
        )

        # Then
        assert reward.reward_id is not None
        assert reward.user_id == user_id
        assert reward.reward_type == reward_type
        assert reward.amount == amount
        assert reward.reference_date == reference_date
        assert reward.point_transaction_id is None
        assert reward.created_at is not None

    def test_create_reward_generates_id(self, tz: ZoneInfo):
        """보상 생성 시 reward_id가 자동 생성된다"""
        # Given
        user_id = Id(uuid7())
        reference_date = datetime.now(tz).date()

        # When
        reward = Reward.create(
            user_id=user_id,
            reward_type=RewardType.DAILY_LOGIN,
            amount=100,
            reference_date=reference_date,
        )

        # Then
        assert reward.reward_id is not None
        assert isinstance(reward.reward_id, Id)

    def test_create_reward_with_different_dates(self, tz: ZoneInfo):
        """다른 날짜로 보상을 생성할 수 있다"""
        # Given
        user_id = Id(uuid7())
        today = datetime.now(tz).date()
        yesterday = today - timedelta(days=1)

        # When
        reward_today = Reward.create(
            user_id=user_id,
            reward_type=RewardType.DAILY_LOGIN,
            amount=100,
            reference_date=today,
        )
        reward_yesterday = Reward.create(
            user_id=user_id,
            reward_type=RewardType.DAILY_LOGIN,
            amount=100,
            reference_date=yesterday,
        )

        # Then
        assert reward_today.reference_date == today
        assert reward_yesterday.reference_date == yesterday
        assert reward_today.reference_date != reward_yesterday.reference_date

    def test_create_reward_point_transaction_id_is_none_initially(self, tz: ZoneInfo):
        """보상 생성 시 point_transaction_id는 None이다"""
        # Given
        user_id = Id(uuid7())
        reference_date = datetime.now(tz).date()

        # When
        reward = Reward.create(
            user_id=user_id,
            reward_type=RewardType.DAILY_LOGIN,
            amount=100,
            reference_date=reference_date,
        )

        # Then
        assert reward.point_transaction_id is None

    def test_reward_point_transaction_id_can_be_set(self, tz: ZoneInfo):
        """보상에 point_transaction_id를 설정할 수 있다"""
        # Given
        user_id = Id(uuid7())
        reference_date = datetime.now(tz).date()
        point_transaction_id = Id(uuid7())

        reward = Reward.create(
            user_id=user_id,
            reward_type=RewardType.DAILY_LOGIN,
            amount=100,
            reference_date=reference_date,
        )

        # When
        reward.point_transaction_id = point_transaction_id

        # Then
        assert reward.point_transaction_id == point_transaction_id

    def test_create_reward_with_different_amounts(self, tz: ZoneInfo):
        """다양한 금액으로 보상을 생성할 수 있다"""
        # Given
        user_id = Id(uuid7())
        reference_date = datetime.now(tz).date()
        amounts = [50, 100, 500, 1000, 2000]

        # When/Then
        for amount in amounts:
            reward = Reward.create(
                user_id=user_id,
                reward_type=RewardType.DAILY_LOGIN,
                amount=amount,
                reference_date=reference_date,
            )
            assert reward.amount == amount
