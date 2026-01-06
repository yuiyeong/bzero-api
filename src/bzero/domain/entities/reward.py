from dataclasses import dataclass
from datetime import UTC, date, datetime

from bzero.domain.value_objects.common import Id
from bzero.domain.value_objects.reward import RewardType


@dataclass
class Reward:
    """보상 엔티티.

    Attributes:
        reward_id: 보상 고유 식별자 (UUID v7)
        user_id: 보상을 받은 사용자 ID
        reward_type: 보상 유형 (DAILY_LOGIN 등)
        amount: 지급 포인트
        reference_date: 기준 날짜 (KST)
        point_transaction_id: 연결된 포인트 트랜잭션 ID
        created_at: 생성 일시
    """

    reward_id: Id
    user_id: Id
    reward_type: RewardType
    amount: int
    reference_date: date
    point_transaction_id: Id | None
    created_at: datetime

    @classmethod
    def create(
        cls,
        user_id: Id,
        reward_type: RewardType,
        amount: int,
        reference_date: date,
    ) -> "Reward":
        """새 보상 엔티티를 생성합니다 (ID 자동 생성).

        Args:
            user_id: 보상을 받을 사용자 ID
            reward_type: 보상 유형
            amount: 지급 포인트
            reference_date: 기준 날짜 (KST)

        Returns:
            새로 생성된 Reward 엔티티
        """
        return cls(
            reward_id=Id(),
            user_id=user_id,
            reward_type=reward_type,
            amount=amount,
            reference_date=reference_date,
            point_transaction_id=None,
            created_at=datetime.now(UTC),
        )
