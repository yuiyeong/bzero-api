from abc import ABC, abstractmethod
from datetime import date

from bzero.domain.entities.reward import Reward
from bzero.domain.value_objects.common import Id
from bzero.domain.value_objects.reward import RewardType


class RewardRepository(ABC):
    """보상 리포지토리 인터페이스 (비동기)."""

    @abstractmethod
    async def create(self, reward: Reward) -> Reward:
        """보상을 생성합니다.

        Args:
            reward: 생성할 보상 엔티티

        Returns:
            생성된 보상 엔티티
        """

    @abstractmethod
    async def exists_by_user_type_date(self, user_id: Id, reward_type: RewardType, reference_date: date) -> bool:
        """해당 사용자가 특정 날짜에 특정 유형의 보상을 받았는지 확인합니다.

        Args:
            user_id: 사용자 ID
            reward_type: 보상 유형
            reference_date: 기준 날짜

        Returns:
            존재 여부
        """

    @abstractmethod
    async def find_by_user_type_date(self, user_id: Id, reward_type: RewardType, reference_date: date) -> Reward | None:
        """해당 사용자의 특정 날짜, 특정 유형 보상을 조회합니다.

        Args:
            user_id: 사용자 ID
            reward_type: 보상 유형
            reference_date: 기준 날짜

        Returns:
            보상 엔티티 또는 None
        """
