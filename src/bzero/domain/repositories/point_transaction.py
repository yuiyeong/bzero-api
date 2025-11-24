from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from bzero.domain.entities.point_transaction import PointTransaction
from bzero.domain.value_objects import Balance, Id, TransactionReference
from bzero.domain.value_objects.point_transaction import TransactionReason, TransactionStatus, TransactionType


@dataclass
class TransactionFilter:
    """포인트 거래 조회 필터

    모든 필드는 선택 사항이며, 제공된 필드만 필터링에 사용됩니다.
    """

    user_id: Id | None = None
    transaction_type: TransactionType | None = None
    status: TransactionStatus | None = None
    reference_type: TransactionReference | None = None
    reason: TransactionReason | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class PointTransactionRepository(ABC):
    """포인트 거래 리포지토리 인터페이스"""

    @abstractmethod
    async def create(self, point_transaction: PointTransaction) -> PointTransaction:
        """포인트 거래를 생성하고 저장합니다."""

    @abstractmethod
    async def find_by_id(self, transaction_id: Id) -> PointTransaction | None:
        """거래 ID로 포인트 거래를 조회합니다. 없으면 None을 반환합니다."""

    @abstractmethod
    async def find_by_filter(
        self, transaction_filter: TransactionFilter, limit: int = 100, offset: int = 0
    ) -> list[PointTransaction]:
        """필터 조건에 맞는 포인트 거래 목록을 조회합니다. 페이지네이션을 지원합니다."""

    @abstractmethod
    async def exists_by_reference(self, reference_type: TransactionReference, reference_id: Id) -> bool:
        """특정 참조 엔티티와 연관된 거래가 존재하는지 확인합니다. 중복 지급 방지용."""

    @abstractmethod
    async def count_by_filter(self, transaction_filter: TransactionFilter) -> int:
        """필터 조건에 맞는 포인트 거래의 총 개수를 반환합니다."""

    @abstractmethod
    async def calculate_real_balance_by_user_id(self, user_id: Id) -> Balance:
        """
        사용자의 실제 잔액을 PointTransaction 기록으로부터 계산합니다.
        EARN 거래 합계 - SPEND 거래 합계 (COMPLETED 상태만)
        """
