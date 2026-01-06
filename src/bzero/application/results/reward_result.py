from dataclasses import dataclass
from datetime import datetime

from bzero.domain.entities.reward import Reward


@dataclass(frozen=True)
class RewardResult:
    """보상 조회 결과.

    Attributes:
        reward_id: 보상 ID
        user_id: 사용자 ID
        reward_type: 보상 유형
        amount: 지급 포인트
        reference_date: 기준 날짜 (YYYY-MM-DD)
        claimed: True: 새로 지급, False: 이미 받음
        point_transaction_id: 포인트 트랜잭션 ID (새로 지급 시에만 존재)
        created_at: 생성 시간
    """

    reward_id: str
    user_id: str
    reward_type: str
    amount: int
    reference_date: str
    claimed: bool
    created_at: datetime
    point_transaction_id: str | None = None

    @classmethod
    def create_from(cls, entity: Reward, claimed: bool) -> "RewardResult":
        """Reward 엔티티에서 RewardResult를 생성합니다.

        Args:
            entity: Reward 엔티티
            claimed: True면 새로 지급, False면 이미 받은 보상

        Returns:
            RewardResult 인스턴스
        """
        return cls(
            reward_id=entity.reward_id.to_hex(),
            user_id=entity.user_id.to_hex(),
            reward_type=entity.reward_type.value,
            amount=entity.amount,
            reference_date=entity.reference_date.isoformat(),
            claimed=claimed,
            created_at=entity.created_at,
            point_transaction_id=entity.point_transaction_id.to_hex() if entity.point_transaction_id else None,
        )
