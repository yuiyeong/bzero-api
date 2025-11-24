from dataclasses import dataclass
from datetime import datetime

from bzero.domain.errors import InvalidAmountError, InvalidPointTransactionStatusError
from bzero.domain.value_objects import Balance, Id
from bzero.domain.value_objects.point_transaction import (
    TransactionReason,
    TransactionReference,
    TransactionStatus,
    TransactionType,
)


@dataclass
class PointTransaction:
    point_transaction_id: Id
    user_id: Id
    transaction_type: TransactionType
    amount: int
    reason: TransactionReason
    balance_before: Balance
    balance_after: Balance
    status: TransactionStatus

    created_at: datetime
    updated_at: datetime

    reference_type: TransactionReference | None = None
    reference_id: Id | None = None  # 참조 엔티티의 ID
    description: str | None = None

    def __post_init__(self):
        """amount는 항상 양수여야 함 (거래 타입으로 방향 결정)"""
        if self.amount <= 0:
            raise InvalidAmountError

    def make_completed(self):
        if self.status != TransactionStatus.PENDING:
            raise InvalidPointTransactionStatusError
        self.status = TransactionStatus.COMPLETED

    def make_failed(self):
        if self.status != TransactionStatus.PENDING:
            raise InvalidPointTransactionStatusError
        self.status = TransactionStatus.FAILED

    @classmethod
    def create(
        cls,
        user_id: Id,
        transaction_type: TransactionType,
        amount: int,
        reason: TransactionReason,
        balance_before: Balance,
        balance_after: Balance,
        reference_type: TransactionReference | None,
        reference_id: Id | None,
        description: str | None,
    ) -> "PointTransaction":
        return PointTransaction(
            point_transaction_id=Id(),
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            reason=reason,
            balance_before=balance_before,
            balance_after=balance_after,
            status=TransactionStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )
