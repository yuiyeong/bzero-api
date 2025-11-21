from bzero.domain.entities.point_transaction import PointTransaction
from bzero.domain.entities.user import User
from bzero.domain.errors import DuplicatedRewardError, InvalidAmountError
from bzero.domain.repositories.point_transaction import PointTransactionRepository
from bzero.domain.repositories.user import UserRepository
from bzero.domain.value_objects import Id, TransactionReason, TransactionReference, TransactionType


class PointTransactionService:
    """포인트 거래 도메인 서비스

    PointTransaction이 진실의 원천(Source of Truth)이며,
    User.current_points는 성능을 위한 denormalized 데이터입니다.

    주의: 모든 메서드는 데이터베이스 트랜잭션 내에서 호출되어야 합니다.
    """

    def __init__(self, user_repository: UserRepository, point_transaction_repository: PointTransactionRepository):
        self._user_repository = user_repository
        self._point_transaction_repository = point_transaction_repository

    async def earn_by(
        self,
        user: User,
        amount: int,
        reason: TransactionReason,
        reference_type: TransactionReference | None,
        reference_id: Id | None,
        description: str | None = None,
    ) -> tuple[User, PointTransaction]:
        # 1. 입력 검증
        if amount <= 0:
            raise InvalidAmountError

        # 2. 중복 지급 방지
        if (
            reference_type
            and reference_id
            and await self._point_transaction_repository.exists_by_reference(reference_type, reference_id)
        ):
            raise DuplicatedRewardError

        # 3. 잔액 계산
        balance_before = await self._point_transaction_repository.calculate_real_balance_by_user_id(user.user_id)
        balance_after = balance_before.add(amount)

        # 4. PointTransaction 생성
        point_transaction = PointTransaction.create(
            user_id=user.user_id,
            transaction_type=TransactionType.EARN,
            amount=amount,
            reason=reason,
            balance_before=balance_before,
            balance_after=balance_after,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )

        # 5. 상태를 COMPLETED로 변경
        point_transaction.make_completed()

        # 6. PointTransaction 저장
        updated_point_transaction = await self._point_transaction_repository.create(point_transaction)

        # 7. 사용자 잔액 업데이트
        user.current_points = updated_point_transaction.balance_after
        updated_user = await self._user_repository.update(user)

        return updated_user, updated_point_transaction

    async def spend_by(
        self,
        user: User,
        amount: int,
        reason: TransactionReason,
        reference_type: TransactionReference | None,
        reference_id: Id | None,
        description: str | None = None,
    ) -> tuple[User, PointTransaction]:
        """포인트를 차감합니다.

        Args:
            user: 포인트를 차감할 사용자
            amount: 차감할 포인트 금액 (양수)
            reason: 차감 사유
            reference_type: 참조 엔티티 타입 (선택)
            reference_id: 참조 엔티티 ID (선택)
            description: 설명 (선택)

        Returns:
            업데이트된 사용자와 생성된 포인트 거래

        Raises:
            InvalidAmountError: amount가 0 이하이거나 잔액이 부족한 경우
        """
        # 1. 입력 검증
        if amount <= 0:
            raise InvalidAmountError

        # 2. 잔액 계산
        balance_before = await self._point_transaction_repository.calculate_real_balance_by_user_id(user.user_id)
        # Balance.deduct()가 잔액 부족 시 InvalidAmountError를 발생시킴
        balance_after = balance_before.deduct(amount)

        # 3. PointTransaction 생성
        point_transaction = PointTransaction.create(
            user_id=user.user_id,
            transaction_type=TransactionType.SPEND,
            amount=amount,
            reason=reason,
            balance_before=balance_before,
            balance_after=balance_after,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )

        # 4. 상태를 COMPLETED로 변경
        point_transaction.make_completed()

        # 5. PointTransaction 저장
        updated_point_transaction = await self._point_transaction_repository.create(point_transaction)

        # 6. 사용자 잔액 업데이트
        user.current_points = updated_point_transaction.balance_after
        updated_user = await self._user_repository.update(user)

        return updated_user, updated_point_transaction
