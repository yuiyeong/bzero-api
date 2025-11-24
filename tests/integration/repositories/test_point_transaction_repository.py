"""PointTransactionRepository Integration Tests."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.core.settings import get_settings
from bzero.domain.entities.point_transaction import PointTransaction
from bzero.domain.entities.user import User
from bzero.domain.repositories.point_transaction import TransactionFilter
from bzero.domain.value_objects import Balance, Email, Id, Nickname, Profile
from bzero.domain.value_objects.point_transaction import (
    TransactionReason,
    TransactionReference,
    TransactionStatus,
    TransactionType,
)
from bzero.infrastructure.repositories.point_transaction import SqlAlchemyPointTransactionRepository
from bzero.infrastructure.repositories.user import SqlAlchemyUserRepository


@pytest.fixture
def user_repository(test_session: AsyncSession) -> SqlAlchemyUserRepository:
    """UserRepository fixture를 생성합니다."""
    return SqlAlchemyUserRepository(test_session)


@pytest.fixture
def point_transaction_repository(test_session: AsyncSession) -> SqlAlchemyPointTransactionRepository:
    """PointTransactionRepository fixture를 생성합니다."""
    return SqlAlchemyPointTransactionRepository(test_session)


@pytest.fixture
async def test_user(user_repository: SqlAlchemyUserRepository) -> User:
    """테스트용 사용자를 생성합니다."""
    user = User(
        user_id=Id(),
        email=Email("test@example.com"),
        password_hash="hashed_password",
        nickname=Nickname("테스트유저"),
        profile=Profile("🎉"),
        current_points=Balance(1000),
        created_at=datetime.now(get_settings().timezone),
        updated_at=datetime.now(get_settings().timezone),
        deleted_at=None,
    )
    return await user_repository.create(user)


@pytest.fixture
def sample_point_transaction(test_user: User) -> PointTransaction:
    """테스트용 샘플 포인트 거래를 생성합니다."""
    return PointTransaction(
        point_transaction_id=Id(),
        user_id=test_user.user_id,
        transaction_type=TransactionType.EARN,
        amount=1000,
        reason=TransactionReason.SIGNED_UP,
        balance_before=Balance(0),
        balance_after=Balance(1000),
        status=TransactionStatus.COMPLETED,
        created_at=datetime.now(get_settings().timezone),
        updated_at=datetime.now(get_settings().timezone),
        reference_type=TransactionReference.USERS,
        reference_id=Id(),
        description="회원가입 보너스",
    )


class TestPointTransactionRepositoryCreate:
    """PointTransactionRepository.create() 메서드 테스트."""

    async def test_create_point_transaction(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        sample_point_transaction: PointTransaction,
    ):
        """포인트 거래를 생성하고 저장할 수 있어야 합니다."""
        # When: 포인트 거래를 생성
        created_transaction = await point_transaction_repository.create(sample_point_transaction)

        # Then: 생성된 거래가 반환됨
        assert created_transaction is not None
        assert str(created_transaction.point_transaction_id.value) == str(
            sample_point_transaction.point_transaction_id.value
        )
        assert created_transaction.user_id == sample_point_transaction.user_id
        assert created_transaction.transaction_type == sample_point_transaction.transaction_type
        assert created_transaction.amount == sample_point_transaction.amount
        assert created_transaction.reason == sample_point_transaction.reason
        assert created_transaction.balance_before == sample_point_transaction.balance_before
        assert created_transaction.balance_after == sample_point_transaction.balance_after
        assert created_transaction.status == sample_point_transaction.status

    async def test_create_point_transaction_persists_to_database(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        sample_point_transaction: PointTransaction,
    ):
        """생성된 포인트 거래가 데이터베이스에 저장되어야 합니다."""
        # Given: 포인트 거래를 생성
        created_transaction = await point_transaction_repository.create(sample_point_transaction)

        # When: 생성된 거래를 ID로 조회
        found_transaction = await point_transaction_repository.find_by_id(created_transaction.point_transaction_id)

        # Then: 동일한 거래가 조회됨
        assert found_transaction is not None
        assert found_transaction.point_transaction_id == created_transaction.point_transaction_id
        assert found_transaction.user_id == created_transaction.user_id
        assert found_transaction.amount == created_transaction.amount

    async def test_create_point_transaction_without_optional_fields(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        test_user: User,
    ):
        """선택 필드(reference, description) 없이도 거래를 생성할 수 있어야 합니다."""
        # Given: 선택 필드가 없는 포인트 거래
        transaction = PointTransaction(
            point_transaction_id=Id(),
            user_id=test_user.user_id,
            transaction_type=TransactionType.EARN,
            amount=50,
            reason=TransactionReason.DIARY,
            balance_before=Balance(1000),
            balance_after=Balance(1050),
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
            reference_type=None,
            reference_id=None,
            description=None,
        )

        # When: 거래를 생성
        created_transaction = await point_transaction_repository.create(transaction)

        # Then: 정상적으로 생성됨
        assert created_transaction is not None
        assert created_transaction.reference_type is None
        assert created_transaction.reference_id is None
        assert created_transaction.description is None


class TestPointTransactionRepositoryFindById:
    """PointTransactionRepository.find_by_id() 메서드 테스트."""

    async def test_find_by_id_success(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        sample_point_transaction: PointTransaction,
    ):
        """존재하는 포인트 거래를 ID로 조회할 수 있어야 합니다."""
        # Given: 포인트 거래를 생성
        created_transaction = await point_transaction_repository.create(sample_point_transaction)

        # When: 거래 ID로 조회
        found_transaction = await point_transaction_repository.find_by_id(created_transaction.point_transaction_id)

        # Then: 거래가 조회됨
        assert found_transaction is not None
        assert found_transaction.point_transaction_id == created_transaction.point_transaction_id
        assert found_transaction.user_id == created_transaction.user_id
        assert found_transaction.amount == created_transaction.amount

    async def test_find_by_id_not_found(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
    ):
        """존재하지 않는 거래 ID로 조회하면 None을 반환해야 합니다."""
        # Given: 존재하지 않는 거래 ID
        nonexistent_id = Id()

        # When: 존재하지 않는 ID로 조회
        found_transaction = await point_transaction_repository.find_by_id(nonexistent_id)

        # Then: None이 반환됨
        assert found_transaction is None


class TestPointTransactionRepositoryFindByFilter:
    """PointTransactionRepository.find_by_filter() 메서드 테스트."""

    @pytest.fixture
    async def multiple_transactions(
        self,
        user_repository: SqlAlchemyUserRepository,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
    ) -> list[PointTransaction]:
        """다양한 포인트 거래들을 생성합니다."""
        # User 1과 User 2 생성
        user1 = User(
            user_id=Id(),
            email=Email("user1@example.com"),
            password_hash="hashed_password",
            nickname=Nickname("유저1"),
            profile=Profile("🎉"),
            current_points=Balance(1000),
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
            deleted_at=None,
        )
        user2 = User(
            user_id=Id(),
            email=Email("user2@example.com"),
            password_hash="hashed_password",
            nickname=Nickname("유저2"),
            profile=Profile("🎊"),
            current_points=Balance(1000),
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
            deleted_at=None,
        )
        user1 = await user_repository.create(user1)
        user2 = await user_repository.create(user2)

        user1_id = user1.user_id
        user2_id = user2.user_id

        # Note: created_at과 updated_at은 DB의 server_default에서 자동 설정됩니다.
        # 엔티티에 설정한 값은 _to_model에서 무시되고, DB가 현재 시간을 설정합니다.
        now = datetime.now(get_settings().timezone)

        transactions = [
            # User 1의 거래들
            PointTransaction(
                point_transaction_id=Id(),
                user_id=user1_id,
                transaction_type=TransactionType.EARN,
                amount=1000,
                reason=TransactionReason.SIGNED_UP,
                balance_before=Balance(0),
                balance_after=Balance(1000),
                status=TransactionStatus.COMPLETED,
                created_at=now,
                updated_at=now,
                reference_type=TransactionReference.USERS,
                reference_id=user1_id,
                description="회원가입 보너스",
            ),
            PointTransaction(
                point_transaction_id=Id(),
                user_id=user1_id,
                transaction_type=TransactionType.EARN,
                amount=50,
                reason=TransactionReason.DIARY,
                balance_before=Balance(1000),
                balance_after=Balance(1050),
                status=TransactionStatus.COMPLETED,
                created_at=now,
                updated_at=now,
                reference_type=TransactionReference.DIARIES,
                reference_id=Id(),
                description="일기 작성 보상",
            ),
            PointTransaction(
                point_transaction_id=Id(),
                user_id=user1_id,
                transaction_type=TransactionType.SPEND,
                amount=300,
                reason=TransactionReason.TICKET,
                balance_before=Balance(1050),
                balance_after=Balance(750),
                status=TransactionStatus.COMPLETED,
                created_at=now,
                updated_at=now,
                reference_type=TransactionReference.TICKETS,
                reference_id=Id(),
                description="일반 비행선 티켓 구매",
            ),
            # User 2의 거래들
            PointTransaction(
                point_transaction_id=Id(),
                user_id=user2_id,
                transaction_type=TransactionType.EARN,
                amount=1000,
                reason=TransactionReason.SIGNED_UP,
                balance_before=Balance(0),
                balance_after=Balance(1000),
                status=TransactionStatus.COMPLETED,
                created_at=now,
                updated_at=now,
                reference_type=TransactionReference.USERS,
                reference_id=user2_id,
                description="회원가입 보너스",
            ),
            # 실패한 거래
            PointTransaction(
                point_transaction_id=Id(),
                user_id=user1_id,
                transaction_type=TransactionType.SPEND,
                amount=2000,
                reason=TransactionReason.TICKET,
                balance_before=Balance(750),
                balance_after=Balance(750),
                status=TransactionStatus.FAILED,
                created_at=now,
                updated_at=now,
                reference_type=TransactionReference.TICKETS,
                reference_id=Id(),
                description="잔액 부족으로 실패",
            ),
        ]

        created_transactions = []
        for transaction in transactions:
            created = await point_transaction_repository.create(transaction)
            created_transactions.append(created)

        return created_transactions

    async def test_find_by_filter_no_filter(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """필터 없이 조회하면 모든 거래가 조회되어야 합니다."""
        # Given: 필터 없음
        transaction_filter = TransactionFilter()

        # When: 필터 없이 조회
        transactions = await point_transaction_repository.find_by_filter(transaction_filter)

        # Then: 모든 거래가 조회됨 (최신순)
        assert len(transactions) == 5
        # 최신 거래가 먼저 나와야 함
        for i in range(len(transactions) - 1):
            assert transactions[i].created_at >= transactions[i + 1].created_at

    async def test_find_by_filter_by_user_id(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """특정 사용자의 거래만 필터링할 수 있어야 합니다."""
        # Given: User 1의 거래만 필터링
        user1_id = multiple_transactions[0].user_id
        transaction_filter = TransactionFilter(user_id=user1_id)

        # When: User 1의 거래만 조회
        transactions = await point_transaction_repository.find_by_filter(transaction_filter)

        # Then: User 1의 거래만 조회됨 (4개)
        assert len(transactions) == 4
        assert all(t.user_id == user1_id for t in transactions)

    async def test_find_by_filter_by_transaction_type(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """거래 타입으로 필터링할 수 있어야 합니다."""
        # Given: EARN 타입만 필터링
        transaction_filter = TransactionFilter(transaction_type=TransactionType.EARN)

        # When: EARN 타입 거래만 조회
        transactions = await point_transaction_repository.find_by_filter(transaction_filter)

        # Then: EARN 타입 거래만 조회됨 (3개)
        assert len(transactions) == 3
        assert all(t.transaction_type == TransactionType.EARN for t in transactions)

    async def test_find_by_filter_by_status(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """거래 상태로 필터링할 수 있어야 합니다."""
        # Given: COMPLETED 상태만 필터링
        transaction_filter = TransactionFilter(status=TransactionStatus.COMPLETED)

        # When: COMPLETED 상태 거래만 조회
        transactions = await point_transaction_repository.find_by_filter(transaction_filter)

        # Then: COMPLETED 상태 거래만 조회됨 (4개)
        assert len(transactions) == 4
        assert all(t.status == TransactionStatus.COMPLETED for t in transactions)

    async def test_find_by_filter_by_reason(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """거래 사유로 필터링할 수 있어야 합니다."""
        # Given: SIGNED_UP 사유만 필터링
        transaction_filter = TransactionFilter(reason=TransactionReason.SIGNED_UP)

        # When: SIGNED_UP 사유 거래만 조회
        transactions = await point_transaction_repository.find_by_filter(transaction_filter)

        # Then: SIGNED_UP 사유 거래만 조회됨 (2개)
        assert len(transactions) == 2
        assert all(t.reason == TransactionReason.SIGNED_UP for t in transactions)

    async def test_find_by_filter_by_reference_type(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """참조 타입으로 필터링할 수 있어야 합니다."""
        # Given: ticket 참조 타입만 필터링
        transaction_filter = TransactionFilter(reference_type=TransactionReference.TICKETS)

        # When: ticket 참조 타입 거래만 조회
        transactions = await point_transaction_repository.find_by_filter(transaction_filter)

        # Then: ticket 참조 타입 거래만 조회됨 (2개)
        assert len(transactions) == 2
        assert all(t.reference_type == TransactionReference.TICKETS for t in transactions)

    async def test_find_by_filter_by_date_range(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """날짜 범위로 필터링할 수 있어야 합니다."""
        # Given: 과거 날짜를 start_date로 설정하여 모든 거래가 조회되도록 함
        start_date = datetime.now(get_settings().timezone) - timedelta(days=1)
        transaction_filter = TransactionFilter(start_date=start_date)

        # When: 해당 날짜 이후 거래만 조회
        transactions = await point_transaction_repository.find_by_filter(transaction_filter)

        # Then: start_date 이후 거래만 조회됨 (모든 거래가 방금 생성되었으므로 5개 모두 조회됨)
        assert len(transactions) == 5
        assert all(t.created_at >= start_date for t in transactions)

    async def test_find_by_filter_by_date_range_with_end_date(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """시작일과 종료일로 범위를 지정할 수 있어야 합니다."""
        # Given: 과거부터 미래까지의 범위로 필터링
        start_date = datetime.now(get_settings().timezone) - timedelta(days=1)
        end_date = datetime.now(get_settings().timezone) + timedelta(days=1)
        transaction_filter = TransactionFilter(start_date=start_date, end_date=end_date)

        # When: 해당 범위의 거래만 조회
        transactions = await point_transaction_repository.find_by_filter(transaction_filter)

        # Then: 모든 거래가 해당 범위에 포함됨 (5개)
        assert len(transactions) == 5
        assert all(start_date <= t.created_at <= end_date for t in transactions)

    async def test_find_by_filter_with_multiple_conditions(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """여러 조건을 조합하여 필터링할 수 있어야 합니다."""
        # Given: User 1의 COMPLETED 상태 EARN 타입 거래만 필터링
        user1_id = multiple_transactions[0].user_id
        transaction_filter = TransactionFilter(
            user_id=user1_id,
            transaction_type=TransactionType.EARN,
            status=TransactionStatus.COMPLETED,
        )

        # When: 복합 조건으로 조회
        transactions = await point_transaction_repository.find_by_filter(transaction_filter)

        # Then: 조건을 모두 만족하는 거래만 조회됨 (2개)
        assert len(transactions) == 2
        assert all(
            t.user_id == user1_id
            and t.transaction_type == TransactionType.EARN
            and t.status == TransactionStatus.COMPLETED
            for t in transactions
        )

    async def test_find_by_filter_with_pagination(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """페이지네이션을 지원해야 합니다."""
        # Given: 필터 없음, 페이지 크기 2
        transaction_filter = TransactionFilter()

        # When: 첫 번째 페이지 조회 (limit=2, offset=0)
        page1 = await point_transaction_repository.find_by_filter(transaction_filter, limit=2, offset=0)

        # When: 두 번째 페이지 조회 (limit=2, offset=2)
        page2 = await point_transaction_repository.find_by_filter(transaction_filter, limit=2, offset=2)

        # Then: 각 페이지에 2개씩 조회됨
        assert len(page1) == 2
        assert len(page2) == 2
        # 페이지 간 거래가 중복되지 않아야 함
        assert page1[0].point_transaction_id != page2[0].point_transaction_id
        assert page1[1].point_transaction_id != page2[1].point_transaction_id

    async def test_find_by_filter_returns_empty_list_when_no_match(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """조건에 맞는 거래가 없으면 빈 리스트를 반환해야 합니다."""
        # Given: 존재하지 않는 사용자 ID로 필터링
        nonexistent_user_id = Id()
        transaction_filter = TransactionFilter(user_id=nonexistent_user_id)

        # When: 조회
        transactions = await point_transaction_repository.find_by_filter(transaction_filter)

        # Then: 빈 리스트 반환
        assert transactions == []


class TestPointTransactionRepositoryExistsByReference:
    """PointTransactionRepository.exists_by_reference() 메서드 테스트."""

    async def test_exists_by_reference_true(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        sample_point_transaction: PointTransaction,
    ):
        """참조 엔티티와 연관된 거래가 존재하면 True를 반환해야 합니다."""
        # Given: 거래를 생성
        created_transaction = await point_transaction_repository.create(sample_point_transaction)

        # When: 해당 참조로 존재 여부 확인
        exists = await point_transaction_repository.exists_by_reference(
            reference_type=created_transaction.reference_type,
            reference_id=created_transaction.reference_id,
        )

        # Then: True 반환
        assert exists is True

    async def test_exists_by_reference_false(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
    ):
        """참조 엔티티와 연관된 거래가 없으면 False를 반환해야 합니다."""
        # Given: 존재하지 않는 참조
        nonexistent_reference_id = Id()

        # When: 존재하지 않는 참조로 확인
        exists = await point_transaction_repository.exists_by_reference(
            reference_type=TransactionReference.DIARIES,
            reference_id=nonexistent_reference_id,
        )

        # Then: False 반환
        assert exists is False

    async def test_exists_by_reference_prevents_duplicate_rewards(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        test_user: User,
    ):
        """중복 지급을 방지하기 위해 사용할 수 있어야 합니다."""
        # Given: 일기 작성 보상을 지급
        diary_id = Id()
        transaction = PointTransaction(
            point_transaction_id=Id(),
            user_id=test_user.user_id,
            transaction_type=TransactionType.EARN,
            amount=50,
            reason=TransactionReason.DIARY,
            balance_before=Balance(1000),
            balance_after=Balance(1050),
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
            reference_type=TransactionReference.DIARIES,
            reference_id=diary_id,
            description="일기 작성 보상",
        )
        await point_transaction_repository.create(transaction)

        # When: 같은 일기에 대한 보상이 이미 지급되었는지 확인
        already_rewarded = await point_transaction_repository.exists_by_reference(
            reference_type=TransactionReference.DIARIES,
            reference_id=diary_id,
        )

        # Then: True 반환 (이미 지급됨)
        assert already_rewarded is True


class TestPointTransactionRepositoryCountByFilter:
    """PointTransactionRepository.count_by_filter() 메서드 테스트."""

    @pytest.fixture
    async def multiple_transactions(
        self,
        user_repository: SqlAlchemyUserRepository,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
    ) -> list[PointTransaction]:
        """다양한 포인트 거래들을 생성합니다."""
        # User 생성
        user = User(
            user_id=Id(),
            email=Email("counter@example.com"),
            password_hash="hashed_password",
            nickname=Nickname("카운터"),
            profile=Profile("🎯"),
            current_points=Balance(1000),
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
            deleted_at=None,
        )
        user = await user_repository.create(user)
        user_id = user.user_id

        transactions = [
            PointTransaction(
                point_transaction_id=Id(),
                user_id=user_id,
                transaction_type=TransactionType.EARN,
                amount=1000,
                reason=TransactionReason.SIGNED_UP,
                balance_before=Balance(0),
                balance_after=Balance(1000),
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(get_settings().timezone),
                updated_at=datetime.now(get_settings().timezone),
            ),
            PointTransaction(
                point_transaction_id=Id(),
                user_id=user_id,
                transaction_type=TransactionType.EARN,
                amount=50,
                reason=TransactionReason.DIARY,
                balance_before=Balance(1000),
                balance_after=Balance(1050),
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(get_settings().timezone),
                updated_at=datetime.now(get_settings().timezone),
            ),
            PointTransaction(
                point_transaction_id=Id(),
                user_id=user_id,
                transaction_type=TransactionType.SPEND,
                amount=300,
                reason=TransactionReason.TICKET,
                balance_before=Balance(1050),
                balance_after=Balance(750),
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(get_settings().timezone),
                updated_at=datetime.now(get_settings().timezone),
            ),
        ]

        created_transactions = []
        for transaction in transactions:
            created = await point_transaction_repository.create(transaction)
            created_transactions.append(created)

        return created_transactions

    async def test_count_by_filter_no_filter(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """필터 없이 조회하면 전체 거래 개수를 반환해야 합니다."""
        # Given: 필터 없음
        transaction_filter = TransactionFilter()

        # When: 전체 개수 조회
        count = await point_transaction_repository.count_by_filter(transaction_filter)

        # Then: 전체 개수 반환 (3개)
        assert count == 3

    async def test_count_by_filter_with_user_id(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """특정 사용자의 거래 개수를 조회할 수 있어야 합니다."""
        # Given: 특정 사용자로 필터링
        user_id = multiple_transactions[0].user_id
        transaction_filter = TransactionFilter(user_id=user_id)

        # When: 해당 사용자의 거래 개수 조회
        count = await point_transaction_repository.count_by_filter(transaction_filter)

        # Then: 해당 사용자의 거래 개수 반환 (3개)
        assert count == 3

    async def test_count_by_filter_with_transaction_type(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """특정 거래 타입의 개수를 조회할 수 있어야 합니다."""
        # Given: EARN 타입으로 필터링
        transaction_filter = TransactionFilter(transaction_type=TransactionType.EARN)

        # When: EARN 타입 거래 개수 조회
        count = await point_transaction_repository.count_by_filter(transaction_filter)

        # Then: EARN 타입 거래 개수 반환 (2개)
        assert count == 2

    async def test_count_by_filter_with_multiple_conditions(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """여러 조건을 조합하여 개수를 조회할 수 있어야 합니다."""
        # Given: 특정 사용자의 EARN 타입 거래만 필터링
        user_id = multiple_transactions[0].user_id
        transaction_filter = TransactionFilter(
            user_id=user_id,
            transaction_type=TransactionType.EARN,
        )

        # When: 복합 조건으로 개수 조회
        count = await point_transaction_repository.count_by_filter(transaction_filter)

        # Then: 조건을 만족하는 거래 개수 반환 (2개)
        assert count == 2

    async def test_count_by_filter_returns_zero_when_no_match(
        self,
        point_transaction_repository: SqlAlchemyPointTransactionRepository,
        multiple_transactions: list[PointTransaction],
    ):
        """조건에 맞는 거래가 없으면 0을 반환해야 합니다."""
        # Given: 존재하지 않는 사용자 ID로 필터링
        nonexistent_user_id = Id()
        transaction_filter = TransactionFilter(user_id=nonexistent_user_id)

        # When: 개수 조회
        count = await point_transaction_repository.count_by_filter(transaction_filter)

        # Then: 0 반환
        assert count == 0
