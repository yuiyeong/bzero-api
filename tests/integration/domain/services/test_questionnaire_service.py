"""QuestionnaireService Integration Tests - 모든 메서드 테스트"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.questionnaire import Questionnaire
from bzero.domain.errors import DuplicatedQuestionnaireError, NotFoundQuestionnaireError
from bzero.domain.services.questionnaire import QuestionnaireService
from bzero.domain.value_objects import Id, QuestionAnswer
from bzero.infrastructure.repositories.questionnaire import SqlAlchemyQuestionnaireRepository


@pytest.fixture
def questionnaire_service(test_session: AsyncSession) -> QuestionnaireService:
    """QuestionnaireService fixture를 생성합니다."""
    questionnaire_repo = SqlAlchemyQuestionnaireRepository(test_session)
    timezone = ZoneInfo("Asia/Seoul")
    return QuestionnaireService(questionnaire_repo, timezone)


class TestQuestionnaireServiceCreateQuestionnaire:
    """QuestionnaireService.create_questionnaire() 메서드 테스트"""

    async def test_create_questionnaire_success(self, questionnaire_service: QuestionnaireService):
        """문답지를 성공적으로 생성할 수 있다"""
        # Given
        user_id = Id()
        city_id = Id()
        question_1_answer = QuestionAnswer("답변1")
        question_2_answer = QuestionAnswer("답변2")
        question_3_answer = QuestionAnswer("답변3")

        # When
        questionnaire = await questionnaire_service.create_questionnaire(
            user_id=user_id,
            city_id=city_id,
            question_1_answer=question_1_answer,
            question_2_answer=question_2_answer,
            question_3_answer=question_3_answer,
        )

        # Then
        assert questionnaire is not None
        assert questionnaire.user_id == user_id
        assert questionnaire.city_id == city_id
        assert questionnaire.question_1_answer == question_1_answer
        assert questionnaire.question_2_answer == question_2_answer
        assert questionnaire.question_3_answer == question_3_answer
        assert questionnaire.has_earned_points is False

    async def test_create_questionnaire_duplicate_error(self, questionnaire_service: QuestionnaireService):
        """같은 도시에 문답지를 중복 생성하면 에러 발생"""
        # Given: 문답지를 이미 생성
        user_id = Id()
        city_id = Id()
        await questionnaire_service.create_questionnaire(
            user_id=user_id,
            city_id=city_id,
            question_1_answer=QuestionAnswer("답변1"),
            question_2_answer=QuestionAnswer("답변2"),
            question_3_answer=QuestionAnswer("답변3"),
        )

        # When & Then: 같은 도시에 다시 생성하면 에러
        with pytest.raises(DuplicatedQuestionnaireError):
            await questionnaire_service.create_questionnaire(
                user_id=user_id,
                city_id=city_id,
                question_1_answer=QuestionAnswer("새 답변1"),
                question_2_answer=QuestionAnswer("새 답변2"),
                question_3_answer=QuestionAnswer("새 답변3"),
            )

    async def test_create_questionnaire_different_cities(self, questionnaire_service: QuestionnaireService):
        """같은 사용자가 다른 도시에는 문답지를 생성할 수 있다"""
        # Given
        user_id = Id()
        city_id_1 = Id()
        city_id_2 = Id()

        # When: 두 개의 다른 도시에 문답지 생성
        questionnaire_1 = await questionnaire_service.create_questionnaire(
            user_id=user_id,
            city_id=city_id_1,
            question_1_answer=QuestionAnswer("답변1-1"),
            question_2_answer=QuestionAnswer("답변1-2"),
            question_3_answer=QuestionAnswer("답변1-3"),
        )
        questionnaire_2 = await questionnaire_service.create_questionnaire(
            user_id=user_id,
            city_id=city_id_2,
            question_1_answer=QuestionAnswer("답변2-1"),
            question_2_answer=QuestionAnswer("답변2-2"),
            question_3_answer=QuestionAnswer("답변2-3"),
        )

        # Then: 두 개 모두 성공
        assert questionnaire_1.city_id == city_id_1
        assert questionnaire_2.city_id == city_id_2


class TestQuestionnaireServiceGetQuestionnaireById:
    """QuestionnaireService.get_questionnaire_by_id() 메서드 테스트"""

    async def test_get_questionnaire_by_id_success(self, questionnaire_service: QuestionnaireService):
        """문답지를 ID로 조회할 수 있다"""
        # Given: 문답지 생성
        user_id = Id()
        city_id = Id()
        created = await questionnaire_service.create_questionnaire(
            user_id=user_id,
            city_id=city_id,
            question_1_answer=QuestionAnswer("답변1"),
            question_2_answer=QuestionAnswer("답변2"),
            question_3_answer=QuestionAnswer("답변3"),
        )

        # When: ID로 조회
        found = await questionnaire_service.get_questionnaire_by_id(created.questionnaire_id)

        # Then
        assert found is not None
        assert found.questionnaire_id == created.questionnaire_id
        assert found.question_1_answer == created.question_1_answer

    async def test_get_questionnaire_by_id_not_found(self, questionnaire_service: QuestionnaireService):
        """존재하지 않는 ID로 조회하면 NotFoundQuestionnaireError 발생"""
        # Given: 존재하지 않는 ID
        non_existent_id = Id()

        # When & Then
        with pytest.raises(NotFoundQuestionnaireError):
            await questionnaire_service.get_questionnaire_by_id(non_existent_id)


class TestQuestionnaireServiceGetQuestionnaireByUserAndCity:
    """QuestionnaireService.get_questionnaire_by_user_and_city() 메서드 테스트"""

    async def test_get_questionnaire_by_user_and_city_success(self, questionnaire_service: QuestionnaireService):
        """사용자 ID와 도시 ID로 문답지를 조회할 수 있다"""
        # Given: 문답지 생성
        user_id = Id()
        city_id = Id()
        created = await questionnaire_service.create_questionnaire(
            user_id=user_id,
            city_id=city_id,
            question_1_answer=QuestionAnswer("답변1"),
            question_2_answer=QuestionAnswer("답변2"),
            question_3_answer=QuestionAnswer("답변3"),
        )

        # When: 사용자 ID와 도시 ID로 조회
        found = await questionnaire_service.get_questionnaire_by_user_and_city(user_id, city_id)

        # Then
        assert found is not None
        assert found.questionnaire_id == created.questionnaire_id

    async def test_get_questionnaire_by_user_and_city_not_found(self, questionnaire_service: QuestionnaireService):
        """존재하지 않는 사용자/도시로 조회하면 None 반환"""
        # Given: 존재하지 않는 사용자 ID와 도시 ID
        non_existent_user_id = Id()
        non_existent_city_id = Id()

        # When
        found = await questionnaire_service.get_questionnaire_by_user_and_city(
            non_existent_user_id, non_existent_city_id
        )

        # Then
        assert found is None


class TestQuestionnaireServiceGetQuestionnairesByUser:
    """QuestionnaireService.get_questionnaires_by_user() 메서드 테스트"""

    async def test_get_questionnaires_by_user_success(self, questionnaire_service: QuestionnaireService):
        """사용자의 문답지 목록을 조회할 수 있다"""
        # Given: 같은 사용자의 문답지 3개 생성 (다른 도시)
        user_id = Id()
        for i in range(3):
            await questionnaire_service.create_questionnaire(
                user_id=user_id,
                city_id=Id(),  # 매번 다른 도시 ID
                question_1_answer=QuestionAnswer(f"답변1-{i+1}"),
                question_2_answer=QuestionAnswer(f"답변2-{i+1}"),
                question_3_answer=QuestionAnswer(f"답변3-{i+1}"),
            )

        # When: 문답지 목록 조회
        questionnaires, total = await questionnaire_service.get_questionnaires_by_user(user_id)

        # Then
        assert len(questionnaires) == 3
        assert total == 3

    async def test_get_questionnaires_by_user_with_pagination(self, questionnaire_service: QuestionnaireService):
        """페이지네이션이 정상 작동한다"""
        # Given: 5개의 문답지 생성
        user_id = Id()
        for i in range(5):
            await questionnaire_service.create_questionnaire(
                user_id=user_id,
                city_id=Id(),
                question_1_answer=QuestionAnswer(f"답변1-{i+1}"),
                question_2_answer=QuestionAnswer(f"답변2-{i+1}"),
                question_3_answer=QuestionAnswer(f"답변3-{i+1}"),
            )

        # When: offset=1, limit=2로 조회
        questionnaires, total = await questionnaire_service.get_questionnaires_by_user(user_id, offset=1, limit=2)

        # Then
        assert len(questionnaires) == 2
        assert total == 5

    async def test_get_questionnaires_by_user_empty(self, questionnaire_service: QuestionnaireService):
        """문답지가 없는 사용자는 빈 목록을 반환한다"""
        # Given: 문답지가 없는 사용자
        user_id = Id()

        # When
        questionnaires, total = await questionnaire_service.get_questionnaires_by_user(user_id)

        # Then
        assert questionnaires == []
        assert total == 0

    async def test_get_questionnaires_by_user_sorted_by_created_at(
        self, questionnaire_service: QuestionnaireService
    ):
        """문답지 목록이 created_at 역순으로 정렬된다"""
        # Given: 문답지 3개 생성
        user_id = Id()
        questionnaires_created = []
        for i in range(3):
            q = await questionnaire_service.create_questionnaire(
                user_id=user_id,
                city_id=Id(),
                question_1_answer=QuestionAnswer(f"답변1-{i+1}"),
                question_2_answer=QuestionAnswer(f"답변2-{i+1}"),
                question_3_answer=QuestionAnswer(f"답변3-{i+1}"),
            )
            questionnaires_created.append(q)

        # When: 문답지 목록 조회
        questionnaires, _ = await questionnaire_service.get_questionnaires_by_user(user_id)

        # Then: 최신순 정렬 (마지막 생성이 첫 번째)
        assert questionnaires[0].created_at >= questionnaires[1].created_at
        assert questionnaires[1].created_at >= questionnaires[2].created_at


class TestQuestionnaireServiceMarkPointsEarned:
    """QuestionnaireService.mark_points_earned() 메서드 테스트"""

    async def test_mark_points_earned_success(self, questionnaire_service: QuestionnaireService):
        """포인트 지급 완료 표시를 할 수 있다"""
        # Given: 문답지 생성
        user_id = Id()
        city_id = Id()
        questionnaire = await questionnaire_service.create_questionnaire(
            user_id=user_id,
            city_id=city_id,
            question_1_answer=QuestionAnswer("답변1"),
            question_2_answer=QuestionAnswer("답변2"),
            question_3_answer=QuestionAnswer("답변3"),
        )
        assert questionnaire.has_earned_points is False

        # When: 포인트 지급 완료 표시
        updated = await questionnaire_service.mark_points_earned(questionnaire)

        # Then
        assert updated.has_earned_points is True

    async def test_mark_points_earned_persists(self, questionnaire_service: QuestionnaireService):
        """포인트 지급 완료 표시가 DB에 저장된다"""
        # Given: 문답지 생성 및 포인트 지급 완료
        user_id = Id()
        city_id = Id()
        questionnaire = await questionnaire_service.create_questionnaire(
            user_id=user_id,
            city_id=city_id,
            question_1_answer=QuestionAnswer("답변1"),
            question_2_answer=QuestionAnswer("답변2"),
            question_3_answer=QuestionAnswer("답변3"),
        )
        updated = await questionnaire_service.mark_points_earned(questionnaire)

        # When: 다시 조회
        found = await questionnaire_service.get_questionnaire_by_id(updated.questionnaire_id)

        # Then: 포인트 지급 완료 상태가 유지됨
        assert found.has_earned_points is True
