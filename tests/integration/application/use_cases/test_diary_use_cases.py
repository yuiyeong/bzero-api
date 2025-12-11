"""Diary Use Cases Integration Tests - 핵심 시나리오만 테스트"""

from datetime import date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.use_cases.diaries.create_diary import CreateDiaryUseCase
from bzero.application.use_cases.diaries.get_diaries import GetDiariesUseCase
from bzero.application.use_cases.diaries.get_diary_by_id import GetDiaryByIdUseCase
from bzero.domain.entities.user import User
from bzero.domain.errors import DuplicatedDiaryError, ForbiddenDiaryError, NotFoundDiaryError
from bzero.domain.services.diary import DiaryService
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.services.ticket import TicketService
from bzero.domain.value_objects import Balance, Id
from bzero.infrastructure.repositories.diary import SqlAlchemyDiaryRepository
from bzero.infrastructure.repositories.point_transaction import SqlAlchemyPointTransactionRepository
from bzero.infrastructure.repositories.ticket import SqlAlchemyTicketRepository
from bzero.infrastructure.repositories.user import SqlAlchemyUserRepository


@pytest.fixture
async def test_user(test_session: AsyncSession) -> User:
    """테스트용 사용자를 생성합니다."""
    user_repo = SqlAlchemyUserRepository(test_session)
    user = User(
        user_id=Id(),
        email=None,
        nickname=None,
        profile=None,
        current_points=Balance(1000),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    return await user_repo.create(user)


@pytest.fixture
def diary_service(test_session: AsyncSession) -> DiaryService:
    from zoneinfo import ZoneInfo

    diary_repo = SqlAlchemyDiaryRepository(test_session)
    return DiaryService(diary_repo, ZoneInfo("Asia/Seoul"))


@pytest.fixture
def ticket_service(test_session: AsyncSession) -> TicketService:
    from zoneinfo import ZoneInfo

    ticket_repo = SqlAlchemyTicketRepository(test_session)
    return TicketService(ticket_repo, ZoneInfo("Asia/Seoul"))


@pytest.fixture
def point_transaction_service(test_session: AsyncSession) -> PointTransactionService:
    user_repo = SqlAlchemyUserRepository(test_session)
    pt_repo = SqlAlchemyPointTransactionRepository(test_session)
    return PointTransactionService(user_repo, pt_repo)


class TestCreateDiaryUseCase:
    """CreateDiaryUseCase 테스트 (핵심 시나리오)"""

    async def test_create_diary_success(
        self,
        test_session: AsyncSession,
        test_user: User,
        diary_service: DiaryService,
        ticket_service: TicketService,
        point_transaction_service: PointTransactionService,
    ):
        """일기를 성공적으로 생성할 수 있다"""
        # Given
        use_case = CreateDiaryUseCase(
            session=test_session,
            diary_service=diary_service,
            ticket_service=ticket_service,
            point_transaction_service=point_transaction_service,
        )

        # When
        result = await use_case.execute(
            user_id=test_user.user_id.value,
            content="오늘은 좋은 하루였다.",
            mood="😊",
            title="행복한 하루",
        )

        # Then
        assert result is not None
        assert result.content == "오늘은 좋은 하루였다."
        assert result.mood == "😊"
        assert result.title == "행복한 하루"
        assert result.has_earned_points is True  # 포인트 지급 완료

    async def test_create_diary_duplicate_error(
        self,
        test_session: AsyncSession,
        test_user: User,
        diary_service: DiaryService,
        ticket_service: TicketService,
        point_transaction_service: PointTransactionService,
    ):
        """같은 날짜에 중복 일기 작성 시 에러 발생"""
        # Given: 오늘 일기를 이미 작성
        use_case = CreateDiaryUseCase(
            session=test_session,
            diary_service=diary_service,
            ticket_service=ticket_service,
            point_transaction_service=point_transaction_service,
        )
        await use_case.execute(
            user_id=test_user.user_id.value,
            content="첫 번째 일기",
            mood="😊",
        )

        # When & Then: 같은 날짜에 다시 작성 시도하면 에러
        with pytest.raises(DuplicatedDiaryError):
            await use_case.execute(
                user_id=test_user.user_id.value,
                content="두 번째 일기",
                mood="😊",
            )


class TestGetDiaryByIdUseCase:
    """GetDiaryByIdUseCase 테스트"""

    async def test_get_diary_by_id_success(
        self,
        test_session: AsyncSession,
        test_user: User,
        diary_service: DiaryService,
        ticket_service: TicketService,
        point_transaction_service: PointTransactionService,
    ):
        """일기를 ID로 조회할 수 있다"""
        # Given: 일기 생성
        create_use_case = CreateDiaryUseCase(
            session=test_session,
            diary_service=diary_service,
            ticket_service=ticket_service,
            point_transaction_service=point_transaction_service,
        )
        created_diary = await create_use_case.execute(
            user_id=test_user.user_id.value,
            content="테스트 일기",
            mood="😊",
        )

        # When: 일기 조회
        get_use_case = GetDiaryByIdUseCase(diary_service)
        result = await get_use_case.execute(
            diary_id=created_diary.diary_id,
            user_id=test_user.user_id.value,
        )

        # Then
        assert result.diary_id == created_diary.diary_id
        assert result.content == "테스트 일기"

    async def test_get_diary_by_id_forbidden(
        self,
        test_session: AsyncSession,
        test_user: User,
        diary_service: DiaryService,
        ticket_service: TicketService,
        point_transaction_service: PointTransactionService,
    ):
        """다른 사용자의 일기 조회 시 Forbidden 에러"""
        # Given: 일기 생성
        create_use_case = CreateDiaryUseCase(
            session=test_session,
            diary_service=diary_service,
            ticket_service=ticket_service,
            point_transaction_service=point_transaction_service,
        )
        created_diary = await create_use_case.execute(
            user_id=test_user.user_id.value,
            content="테스트 일기",
            mood="😊",
        )

        # When & Then: 다른 사용자로 조회 시도
        get_use_case = GetDiaryByIdUseCase(diary_service)
        other_user_id = Id().value
        with pytest.raises(ForbiddenDiaryError):
            await get_use_case.execute(
                diary_id=created_diary.diary_id,
                user_id=other_user_id,
            )

    async def test_get_diary_by_id_not_found(
        self,
        test_user: User,
        diary_service: DiaryService,
    ):
        """존재하지 않는 일기 조회 시 NotFound 에러"""
        # Given: 존재하지 않는 일기 ID
        non_existent_id = Id().value

        # When & Then
        get_use_case = GetDiaryByIdUseCase(diary_service)
        with pytest.raises(NotFoundDiaryError):
            await get_use_case.execute(
                diary_id=non_existent_id,
                user_id=test_user.user_id.value,
            )


class TestGetDiariesUseCase:
    """GetDiariesUseCase 테스트"""

    async def test_get_diaries_returns_paginated_result(
        self,
        test_session: AsyncSession,
        test_user: User,
        diary_service: DiaryService,
        ticket_service: TicketService,
        point_transaction_service: PointTransactionService,
    ):
        """일기 목록을 PaginatedResult로 반환한다"""
        # Given: 일기 3개 생성
        create_use_case = CreateDiaryUseCase(
            session=test_session,
            diary_service=diary_service,
            ticket_service=ticket_service,
            point_transaction_service=point_transaction_service,
        )

        # 각 일기를 다른 날짜로 생성 (중복 방지)
        from unittest.mock import patch

        for i in range(3):
            # diary_date를 강제로 다르게 설정
            with patch.object(diary_service, 'calculate_diary_date', return_value=date(2025, 12, 10 + i)):
                await create_use_case.execute(
                    user_id=test_user.user_id.value,
                    content=f"일기 {i+1}",
                    mood="😊",
                )

        # When: 일기 목록 조회
        get_use_case = GetDiariesUseCase(diary_service)
        result = await get_use_case.execute(
            user_id=test_user.user_id.value,
            offset=0,
            limit=20,
        )

        # Then
        assert result.total == 3
        assert len(result.items) == 3
        assert result.offset == 0
        assert result.limit == 20

    async def test_get_diaries_pagination(
        self,
        test_session: AsyncSession,
        test_user: User,
        diary_service: DiaryService,
        ticket_service: TicketService,
        point_transaction_service: PointTransactionService,
    ):
        """페이지네이션이 정상 작동한다"""
        # Given: 일기 5개 생성
        create_use_case = CreateDiaryUseCase(
            session=test_session,
            diary_service=diary_service,
            ticket_service=ticket_service,
            point_transaction_service=point_transaction_service,
        )

        from unittest.mock import patch

        for i in range(5):
            with patch.object(diary_service, 'calculate_diary_date', return_value=date(2025, 12, 10 + i)):
                await create_use_case.execute(
                    user_id=test_user.user_id.value,
                    content=f"일기 {i+1}",
                    mood="😊",
                )

        # When: offset=1, limit=2로 조회
        get_use_case = GetDiariesUseCase(diary_service)
        result = await get_use_case.execute(
            user_id=test_user.user_id.value,
            offset=1,
            limit=2,
        )

        # Then
        assert result.total == 5
        assert len(result.items) == 2
        assert result.offset == 1
        assert result.limit == 2

    async def test_get_diaries_empty(
        self,
        test_user: User,
        diary_service: DiaryService,
    ):
        """일기가 없으면 빈 목록을 반환한다"""
        # When: 일기 목록 조회
        get_use_case = GetDiariesUseCase(diary_service)
        result = await get_use_case.execute(
            user_id=test_user.user_id.value,
            offset=0,
            limit=20,
        )

        # Then
        assert result.total == 0
        assert len(result.items) == 0


class TestGetTodayDiaryUseCase:
    """GetTodayDiaryUseCase 테스트"""

    async def test_get_today_diary_success(
        self,
        test_session: AsyncSession,
        test_user: User,
        diary_service: DiaryService,
        ticket_service: TicketService,
        point_transaction_service: PointTransactionService,
    ):
        """오늘 일기를 조회할 수 있다"""
        # Given: 오늘 일기 생성
        from bzero.application.use_cases.diaries.get_today_diary import GetTodayDiaryUseCase

        create_use_case = CreateDiaryUseCase(
            session=test_session,
            diary_service=diary_service,
            ticket_service=ticket_service,
            point_transaction_service=point_transaction_service,
        )
        created_diary = await create_use_case.execute(
            user_id=test_user.user_id.value,
            content="오늘의 일기",
            mood="😊",
        )

        # When: 오늘 일기 조회
        get_use_case = GetTodayDiaryUseCase(diary_service, ticket_service)
        result = await get_use_case.execute(user_id=test_user.user_id.value)

        # Then
        assert result is not None
        assert result.diary_id == created_diary.diary_id
        assert result.content == "오늘의 일기"

    async def test_get_today_diary_not_found(
        self,
        test_user: User,
        diary_service: DiaryService,
        ticket_service: TicketService,
    ):
        """오늘 일기가 없으면 None을 반환한다"""
        # Given: 일기가 없음
        from bzero.application.use_cases.diaries.get_today_diary import GetTodayDiaryUseCase

        # When: 오늘 일기 조회
        get_use_case = GetTodayDiaryUseCase(diary_service, ticket_service)
        result = await get_use_case.execute(user_id=test_user.user_id.value)

        # Then
        assert result is None
