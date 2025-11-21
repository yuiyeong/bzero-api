from sqlalchemy import case, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from bzero.domain.entities.point_transaction import PointTransaction
from bzero.domain.repositories.point_transaction import PointTransactionRepository, TransactionFilter
from bzero.domain.value_objects import (
    Balance,
    Id,
    TransactionReason,
    TransactionReference,
    TransactionStatus,
    TransactionType,
)
from bzero.infrastructure.db.point_transaction_model import PointTransactionModel


class SqlAlchemyPointTransactionRepository(PointTransactionRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, point_transaction: PointTransaction) -> PointTransaction:
        model = self._to_model(point_transaction)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def find_by_id(self, transaction_id: Id) -> PointTransaction | None:
        stmt = select(PointTransactionModel).where(
            PointTransactionModel.point_transaction_id == transaction_id.value,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_filter(
        self, transaction_filter: TransactionFilter, limit: int = 100, offset: int = 0
    ) -> list[PointTransaction]:
        stmt = select(PointTransactionModel)
        stmt = self._apply_filters(stmt, transaction_filter)
        stmt = stmt.order_by(PointTransactionModel.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def exists_by_reference(self, reference_type: TransactionReference, reference_id: Id) -> bool:
        stmt = select(
            exists().where(
                PointTransactionModel.reference_type == reference_type.value,
                PointTransactionModel.reference_id == reference_id.value,
                PointTransactionModel.status != TransactionStatus.FAILED.value,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar()

    async def count_by_filter(self, transaction_filter: TransactionFilter) -> int:
        stmt = select(func.count()).select_from(PointTransactionModel)
        stmt = self._apply_filters(stmt, transaction_filter)
        result = await self._session.execute(stmt)
        return result.scalar()

    async def calculate_real_balance_by_user_id(self, user_id: Id) -> Balance:
        stmt = select(
            func.coalesce(  # NULL 처리
                func.sum(
                    case(
                        # EARN이면 +amount
                        (
                            PointTransactionModel.transaction_type == TransactionType.EARN.value,
                            PointTransactionModel.amount,
                        ),
                        # SPEND이면 -amount
                        (
                            PointTransactionModel.transaction_type == TransactionType.SPEND.value,
                            -PointTransactionModel.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            )
        ).where(
            PointTransactionModel.user_id == user_id.value,
            PointTransactionModel.status == TransactionStatus.COMPLETED.value,
        )
        result = await self._session.execute(stmt)
        return Balance(result.scalar_one())

    @staticmethod
    def _apply_filters(stmt: Select, transaction_filter: TransactionFilter) -> Select:
        """공통 필터 조건을 WHERE 절에 적용합니다."""
        if transaction_filter.user_id:
            stmt = stmt.where(PointTransactionModel.user_id == transaction_filter.user_id.value)

        if transaction_filter.transaction_type:
            stmt = stmt.where(PointTransactionModel.transaction_type == transaction_filter.transaction_type.value)

        if transaction_filter.status:
            stmt = stmt.where(PointTransactionModel.status == transaction_filter.status.value)

        if transaction_filter.reference_type:
            stmt = stmt.where(PointTransactionModel.reference_type == transaction_filter.reference_type.value)

        if transaction_filter.reason:
            stmt = stmt.where(PointTransactionModel.reason == transaction_filter.reason.value)

        if transaction_filter.start_date:
            stmt = stmt.where(PointTransactionModel.created_at >= transaction_filter.start_date)

        if transaction_filter.end_date:
            stmt = stmt.where(PointTransactionModel.created_at <= transaction_filter.end_date)

        return stmt

    @staticmethod
    def _to_model(entity: PointTransaction) -> PointTransactionModel:
        """도메인 엔티티를 ORM 모델로 변환합니다.

        Note: created_at과 updated_at은 의도적으로 전달하지 않습니다.
        이를 통해 데이터베이스의 server_default (func.current_timestamp())가
        자동으로 현재 시간을 설정하도록 합니다.
        """
        return PointTransactionModel(
            point_transaction_id=entity.point_transaction_id.value,
            user_id=entity.user_id.value,
            transaction_type=entity.transaction_type.value,
            amount=entity.amount,
            reason=entity.reason.value,
            balance_before=entity.balance_before.value,
            balance_after=entity.balance_after.value,
            status=entity.status.value,
            reference_type=entity.reference_type.value if entity.reference_type else None,
            reference_id=entity.reference_id.value if entity.reference_id else None,
            description=entity.description,
        )

    @staticmethod
    def _to_entity(model: PointTransactionModel) -> PointTransaction:
        return PointTransaction(
            point_transaction_id=Id(model.point_transaction_id),
            user_id=Id(model.user_id),
            transaction_type=TransactionType(model.transaction_type),
            amount=model.amount,
            reason=TransactionReason(model.reason),
            balance_before=Balance(model.balance_before),
            balance_after=Balance(model.balance_after),
            status=TransactionStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            reference_type=TransactionReference(model.reference_type) if model.reference_type else None,
            reference_id=Id(model.reference_id) if model.reference_id else None,
            description=model.description,
        )
