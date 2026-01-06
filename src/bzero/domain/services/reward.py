from datetime import date, datetime
from zoneinfo import ZoneInfo

from bzero.domain.entities.reward import Reward
from bzero.domain.errors import AlreadyClaimedRewardError, NotFoundUserError
from bzero.domain.repositories.reward import RewardRepository
from bzero.domain.repositories.user import UserRepository
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.value_objects.common import Id
from bzero.domain.value_objects.point_transaction import (
    TransactionReason,
    TransactionReference,
)
from bzero.domain.value_objects.reward import RewardType


class RewardService:
    """보상 도메인 서비스

    일일 출석 보상 등 각종 보상 지급을 담당합니다.

    주의: 모든 메서드는 데이터베이스 트랜잭션 내에서 호출되어야 합니다.
    """

    DAILY_LOGIN_REWARD_AMOUNT = 100

    def __init__(
        self,
        reward_repository: RewardRepository,
        user_repository: UserRepository,
        point_transaction_service: PointTransactionService,
        timezone: ZoneInfo,
    ):
        self._reward_repository = reward_repository
        self._user_repository = user_repository
        self._point_transaction_service = point_transaction_service
        self._timezone = timezone

    async def claim_daily_login(self, user_id: Id) -> Reward:
        """일일 출석 보상을 수령합니다.

        Args:
            user_id: 보상을 받을 사용자 ID

        Returns:
            생성된 보상 엔티티

        Raises:
            AlreadyClaimedRewardError: 이미 오늘 보상을 받은 경우
            NotFoundUserError: 사용자를 찾을 수 없는 경우
        """
        today_kst = self._get_today_kst()

        # 중복 체크
        existing = await self._reward_repository.find_by_user_type_date(user_id, RewardType.DAILY_LOGIN, today_kst)
        if existing:
            raise AlreadyClaimedRewardError

        # 사용자 조회
        user = await self._user_repository.find_by_user_id(user_id)
        if user is None:
            raise NotFoundUserError

        # 보상 생성
        reward = Reward.create(
            user_id=user_id,
            reward_type=RewardType.DAILY_LOGIN,
            amount=self.DAILY_LOGIN_REWARD_AMOUNT,
            reference_date=today_kst,
        )

        # 포인트 지급
        _, point_tx = await self._point_transaction_service.earn_by(
            user=user,
            amount=self.DAILY_LOGIN_REWARD_AMOUNT,
            reason=TransactionReason.DAILY_LOGIN,
            reference_type=TransactionReference.REWARDS,
            reference_id=reward.reward_id,
            description="일일 출석 보상",
        )

        reward.point_transaction_id = point_tx.point_transaction_id
        return await self._reward_repository.create(reward)

    async def get_today_reward(self, user_id: Id, reward_type: RewardType) -> Reward | None:
        """오늘 보상을 조회합니다.

        Args:
            user_id: 사용자 ID
            reward_type: 보상 유형

        Returns:
            보상 엔티티 또는 None
        """
        today_kst = self._get_today_kst()
        return await self._reward_repository.find_by_user_type_date(user_id, reward_type, today_kst)

    def _get_today_kst(self) -> date:
        """KST 기준 오늘 날짜를 반환합니다."""
        return datetime.now(self._timezone).date()
