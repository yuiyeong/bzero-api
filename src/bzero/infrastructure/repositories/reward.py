from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.reward import Reward
from bzero.domain.repositories.reward import RewardRepository
from bzero.domain.value_objects.common import Id
from bzero.domain.value_objects.reward import RewardType
from bzero.infrastructure.db.reward_model import RewardModel


class SqlAlchemyRewardRepository(RewardRepository):
    """SQLAlchemy 기반 Reward Repository (비동기).

    Attributes:
        _session: SQLAlchemy AsyncSession 인스턴스
    """

    def __init__(self, session: AsyncSession):
        """리포지토리를 초기화합니다.

        Args:
            session: SQLAlchemy AsyncSession 인스턴스
        """
        self._session = session

    async def create(self, reward: Reward) -> Reward:
        """보상을 생성합니다.

        Args:
            reward: 생성할 보상 엔티티

        Returns:
            생성된 보상 엔티티
        """
        model = self._to_model(reward)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def exists_by_user_type_date(self, user_id: Id, reward_type: RewardType, reference_date: date) -> bool:
        """해당 사용자가 특정 날짜에 특정 유형의 보상을 받았는지 확인합니다.

        Args:
            user_id: 사용자 ID
            reward_type: 보상 유형
            reference_date: 기준 날짜

        Returns:
            존재 여부
        """
        stmt = select(RewardModel.reward_id).where(
            RewardModel.user_id == user_id.value,
            RewardModel.reward_type == reward_type.value,
            RewardModel.reference_date == reference_date,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def find_by_user_type_date(self, user_id: Id, reward_type: RewardType, reference_date: date) -> Reward | None:
        """해당 사용자의 특정 날짜, 특정 유형 보상을 조회합니다.

        Args:
            user_id: 사용자 ID
            reward_type: 보상 유형
            reference_date: 기준 날짜

        Returns:
            보상 엔티티 또는 None
        """
        stmt = select(RewardModel).where(
            RewardModel.user_id == user_id.value,
            RewardModel.reward_type == reward_type.value,
            RewardModel.reference_date == reference_date,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_model(entity: Reward) -> RewardModel:
        """Reward 엔티티를 RewardModel로 변환합니다."""
        return RewardModel(
            reward_id=entity.reward_id.value,
            user_id=entity.user_id.value,
            reward_type=entity.reward_type.value,
            amount=entity.amount,
            reference_date=entity.reference_date,
            point_transaction_id=entity.point_transaction_id.value if entity.point_transaction_id else None,
            created_at=entity.created_at,
        )

    @staticmethod
    def _to_entity(model: RewardModel) -> Reward:
        """RewardModel을 Reward 엔티티로 변환합니다."""
        return Reward(
            reward_id=Id(model.reward_id),
            user_id=Id(model.user_id),
            reward_type=RewardType(model.reward_type),
            amount=model.amount,
            reference_date=model.reference_date,
            point_transaction_id=Id(model.point_transaction_id) if model.point_transaction_id else None,
            created_at=model.created_at,
        )
