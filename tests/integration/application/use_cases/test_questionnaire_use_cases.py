"""Questionnaire Use Cases Integration Tests - 모든 시나리오 테스트"""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.use_cases.questionnaires.create_questionnaire import CreateQuestionnaireUseCase
from bzero.application.use_cases.questionnaires.get_questionnaire_by_id import GetQuestionnaireByIdUseCase
from bzero.application.use_cases.questionnaires.get_questionnaires import GetQuestionnairesUseCase
from bzero.domain.entities.user import User
from bzero.domain.errors import DuplicatedQuestionnaireError, ForbiddenQuestionnaireError, NotFoundQuestionnaireError
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.services.questionnaire import QuestionnaireService
from bzero.domain.value_objects import Balance, Id
from bzero.infrastructure.repositories.point_transaction import SqlAlchemyPointTransactionRepository
from bzero.infrastructure.repositories.questionnaire import SqlAlchemyQuestionnaireRepository
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
def questionnaire_service(test_session: AsyncSession) -> QuestionnaireService:
    from zoneinfo import ZoneInfo

    questionnaire_repo = SqlAlchemyQuestionnaireRepository(test_session)
    return QuestionnaireService(questionnaire_repo, ZoneInfo("Asia/Seoul"))


@pytest.fixture
def point_transaction_service(test_session: AsyncSession) -> PointTransactionService:
    user_repo = SqlAlchemyUserRepository(test_session)
    pt_repo = SqlAlchemyPointTransactionRepository(test_session)
    return PointTransactionService(user_repo, pt_repo)


class TestCreateQuestionnaireUseCase:
    """CreateQuestionnaireUseCase 테스트"""

    async def test_create_questionnaire_success(
        self,
        test_session: AsyncSession,
        test_user: User,
        questionnaire_service: QuestionnaireService,
        point_transaction_service: PointTransactionService,
    ):
        """문답지를 성공적으로 생성할 수 있다"""
        # Given
        use_case = CreateQuestionnaireUseCase(
            session=test_session,
            questionnaire_service=questionnaire_service,
            point_transaction_service=point_transaction_service,
        )
        city_id = Id().value

        # When
        result = await use_case.execute(
            user_id=test_user.user_id.value,
            city_id=city_id,
            question_1_answer="답변1",
            question_2_answer="답변2",
            question_3_answer="답변3",
        )

        # Then
        assert result is not None
        assert result.city_id == city_id
        assert result.question_1_answer == "답변1"
        assert result.question_2_answer == "답변2"
        assert result.question_3_answer == "답변3"
        assert result.has_earned_points is True  # 포인트 지급 완료

    async def test_create_questionnaire_duplicate_error(
        self,
        test_session: AsyncSession,
        test_user: User,
        questionnaire_service: QuestionnaireService,
        point_transaction_service: PointTransactionService,
    ):
        """같은 도시에 중복 문답지 작성 시 에러 발생"""
        # Given: 도시 A에 문답지를 이미 작성
        use_case = CreateQuestionnaireUseCase(
            session=test_session,
            questionnaire_service=questionnaire_service,
            point_transaction_service=point_transaction_service,
        )
        city_id = Id().value
        await use_case.execute(
            user_id=test_user.user_id.value,
            city_id=city_id,
            question_1_answer="첫 번째 답변1",
            question_2_answer="첫 번째 답변2",
            question_3_answer="첫 번째 답변3",
        )

        # When & Then: 같은 도시에 다시 작성 시도하면 에러
        with pytest.raises(DuplicatedQuestionnaireError):
            await use_case.execute(
                user_id=test_user.user_id.value,
                city_id=city_id,
                question_1_answer="두 번째 답변1",
                question_2_answer="두 번째 답변2",
                question_3_answer="두 번째 답변3",
            )

    async def test_create_questionnaire_different_cities(
        self,
        test_session: AsyncSession,
        test_user: User,
        questionnaire_service: QuestionnaireService,
        point_transaction_service: PointTransactionService,
    ):
        """다른 도시에는 문답지를 각각 작성할 수 있다"""
        # Given
        use_case = CreateQuestionnaireUseCase(
            session=test_session,
            questionnaire_service=questionnaire_service,
            point_transaction_service=point_transaction_service,
        )
        city_id_1 = Id().value
        city_id_2 = Id().value

        # When: 두 개의 다른 도시에 문답지 생성
        result_1 = await use_case.execute(
            user_id=test_user.user_id.value,
            city_id=city_id_1,
            question_1_answer="답변1-1",
            question_2_answer="답변1-2",
            question_3_answer="답변1-3",
        )
        result_2 = await use_case.execute(
            user_id=test_user.user_id.value,
            city_id=city_id_2,
            question_1_answer="답변2-1",
            question_2_answer="답변2-2",
            question_3_answer="답변2-3",
        )

        # Then: 두 개 모두 성공
        assert result_1.city_id == city_id_1
        assert result_2.city_id == city_id_2


class TestGetQuestionnaireByIdUseCase:
    """GetQuestionnaireByIdUseCase 테스트"""

    async def test_get_questionnaire_by_id_success(
        self,
        test_session: AsyncSession,
        test_user: User,
        questionnaire_service: QuestionnaireService,
        point_transaction_service: PointTransactionService,
    ):
        """문답지를 ID로 조회할 수 있다"""
        # Given: 문답지 생성
        create_use_case = CreateQuestionnaireUseCase(
            session=test_session,
            questionnaire_service=questionnaire_service,
            point_transaction_service=point_transaction_service,
        )
        created = await create_use_case.execute(
            user_id=test_user.user_id.value,
            city_id=Id().value,
            question_1_answer="답변1",
            question_2_answer="답변2",
            question_3_answer="답변3",
        )

        # When: 문답지 조회
        get_use_case = GetQuestionnaireByIdUseCase(questionnaire_service)
        result = await get_use_case.execute(
            questionnaire_id=created.questionnaire_id,
            user_id=test_user.user_id.value,
        )

        # Then
        assert result.questionnaire_id == created.questionnaire_id
        assert result.question_1_answer == "답변1"

    async def test_get_questionnaire_by_id_forbidden(
        self,
        test_session: AsyncSession,
        test_user: User,
        questionnaire_service: QuestionnaireService,
        point_transaction_service: PointTransactionService,
    ):
        """다른 사용자의 문답지 조회 시 Forbidden 에러"""
        # Given: 문답지 생성
        create_use_case = CreateQuestionnaireUseCase(
            session=test_session,
            questionnaire_service=questionnaire_service,
            point_transaction_service=point_transaction_service,
        )
        created = await create_use_case.execute(
            user_id=test_user.user_id.value,
            city_id=Id().value,
            question_1_answer="답변1",
            question_2_answer="답변2",
            question_3_answer="답변3",
        )

        # When & Then: 다른 사용자로 조회 시도
        get_use_case = GetQuestionnaireByIdUseCase(questionnaire_service)
        other_user_id = Id().value
        with pytest.raises(ForbiddenQuestionnaireError):
            await get_use_case.execute(
                questionnaire_id=created.questionnaire_id,
                user_id=other_user_id,
            )

    async def test_get_questionnaire_by_id_not_found(
        self,
        test_user: User,
        questionnaire_service: QuestionnaireService,
    ):
        """존재하지 않는 문답지 조회 시 NotFound 에러"""
        # Given: 존재하지 않는 문답지 ID
        non_existent_id = Id().value

        # When & Then
        get_use_case = GetQuestionnaireByIdUseCase(questionnaire_service)
        with pytest.raises(NotFoundQuestionnaireError):
            await get_use_case.execute(
                questionnaire_id=non_existent_id,
                user_id=test_user.user_id.value,
            )


class TestGetQuestionnairesUseCase:
    """GetQuestionnairesUseCase 테스트"""

    async def test_get_questionnaires_returns_paginated_result(
        self,
        test_session: AsyncSession,
        test_user: User,
        questionnaire_service: QuestionnaireService,
        point_transaction_service: PointTransactionService,
    ):
        """문답지 목록을 PaginatedResult로 반환한다"""
        # Given: 문답지 3개 생성 (다른 도시)
        create_use_case = CreateQuestionnaireUseCase(
            session=test_session,
            questionnaire_service=questionnaire_service,
            point_transaction_service=point_transaction_service,
        )

        for i in range(3):
            await create_use_case.execute(
                user_id=test_user.user_id.value,
                city_id=Id().value,  # 매번 다른 도시 ID
                question_1_answer=f"답변1-{i+1}",
                question_2_answer=f"답변2-{i+1}",
                question_3_answer=f"답변3-{i+1}",
            )

        # When: 문답지 목록 조회
        get_use_case = GetQuestionnairesUseCase(questionnaire_service)
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

    async def test_get_questionnaires_pagination(
        self,
        test_session: AsyncSession,
        test_user: User,
        questionnaire_service: QuestionnaireService,
        point_transaction_service: PointTransactionService,
    ):
        """페이지네이션이 정상 작동한다"""
        # Given: 문답지 5개 생성
        create_use_case = CreateQuestionnaireUseCase(
            session=test_session,
            questionnaire_service=questionnaire_service,
            point_transaction_service=point_transaction_service,
        )

        for i in range(5):
            await create_use_case.execute(
                user_id=test_user.user_id.value,
                city_id=Id().value,
                question_1_answer=f"답변1-{i+1}",
                question_2_answer=f"답변2-{i+1}",
                question_3_answer=f"답변3-{i+1}",
            )

        # When: offset=1, limit=2로 조회
        get_use_case = GetQuestionnairesUseCase(questionnaire_service)
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

    async def test_get_questionnaires_empty(
        self,
        test_user: User,
        questionnaire_service: QuestionnaireService,
    ):
        """문답지가 없으면 빈 목록을 반환한다"""
        # When: 문답지 목록 조회
        get_use_case = GetQuestionnairesUseCase(questionnaire_service)
        result = await get_use_case.execute(
            user_id=test_user.user_id.value,
            offset=0,
            limit=20,
        )

        # Then
        assert result.total == 0
        assert len(result.items) == 0

    async def test_get_questionnaires_sorted_by_created_at(
        self,
        test_session: AsyncSession,
        test_user: User,
        questionnaire_service: QuestionnaireService,
        point_transaction_service: PointTransactionService,
    ):
        """문답지 목록이 created_at 역순으로 정렬된다"""
        # Given: 문답지 3개 생성
        create_use_case = CreateQuestionnaireUseCase(
            session=test_session,
            questionnaire_service=questionnaire_service,
            point_transaction_service=point_transaction_service,
        )

        questionnaires_created = []
        for i in range(3):
            result = await create_use_case.execute(
                user_id=test_user.user_id.value,
                city_id=Id().value,
                question_1_answer=f"답변1-{i+1}",
                question_2_answer=f"답변2-{i+1}",
                question_3_answer=f"답변3-{i+1}",
            )
            questionnaires_created.append(result)

        # When: 문답지 목록 조회
        get_use_case = GetQuestionnairesUseCase(questionnaire_service)
        result = await get_use_case.execute(
            user_id=test_user.user_id.value,
            offset=0,
            limit=20,
        )

        # Then: 최신순 정렬 (마지막 생성이 첫 번째)
        items = result.items
        assert items[0].created_at >= items[1].created_at
        assert items[1].created_at >= items[2].created_at
