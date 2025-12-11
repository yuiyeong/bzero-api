"""QuestionnaireRepository Integration Tests."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.questionnaire import Questionnaire
from bzero.domain.value_objects import Id, QuestionAnswer
from bzero.infrastructure.repositories.questionnaire import SqlAlchemyQuestionnaireRepository


@pytest.fixture
def questionnaire_repository(test_session: AsyncSession) -> SqlAlchemyQuestionnaireRepository:
    """QuestionnaireRepository fixture를 생성합니다."""
    return SqlAlchemyQuestionnaireRepository(test_session)


@pytest.fixture
def sample_questionnaire() -> Questionnaire:
    """테스트용 샘플 문답지를 생성합니다."""
    return Questionnaire.create(
        user_id=Id(),
        city_id=Id(),
        question_1_answer=QuestionAnswer("답변1"),
        question_2_answer=QuestionAnswer("답변2"),
        question_3_answer=QuestionAnswer("답변3"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestQuestionnaireRepositorySave:
    """QuestionnaireRepository.save() 메서드 테스트."""

    async def test_save_new_questionnaire(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_questionnaire: Questionnaire,
    ):
        """새 문답지를 저장할 수 있어야 합니다."""
        # When: 문답지를 저장
        saved = await questionnaire_repository.save(sample_questionnaire)

        # Then: 저장된 문답지가 반환됨
        assert saved is not None
        assert str(saved.questionnaire_id.value) == str(sample_questionnaire.questionnaire_id.value)
        assert saved.question_1_answer == sample_questionnaire.question_1_answer

    async def test_save_persists_to_database(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_questionnaire: Questionnaire,
    ):
        """저장된 문답지가 데이터베이스에 저장되어야 합니다."""
        # Given: 문답지를 저장
        saved = await questionnaire_repository.save(sample_questionnaire)

        # When: 저장된 문답지를 ID로 조회
        found = await questionnaire_repository.find_by_id(saved.questionnaire_id)

        # Then: 동일한 문답지가 조회됨
        assert found is not None
        assert found.questionnaire_id == saved.questionnaire_id

    async def test_update_existing_questionnaire(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_questionnaire: Questionnaire,
    ):
        """기존 문답지를 업데이트할 수 있어야 합니다."""
        # Given: 문답지를 저장
        saved = await questionnaire_repository.save(sample_questionnaire)

        # When: 포인트 지급 후 저장
        saved.mark_points_earned()
        updated = await questionnaire_repository.save(saved)

        # Then: 업데이트된 내용이 반영됨
        found = await questionnaire_repository.find_by_id(updated.questionnaire_id)
        assert found is not None
        assert found.has_earned_points is True


class TestQuestionnaireRepositoryFindById:
    """QuestionnaireRepository.find_by_id() 메서드 테스트."""

    async def test_find_by_id_success(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_questionnaire: Questionnaire,
    ):
        """존재하는 문답지를 ID로 조회할 수 있어야 합니다."""
        # Given: 문답지를 저장
        saved = await questionnaire_repository.save(sample_questionnaire)

        # When: 문답지 ID로 조회
        found = await questionnaire_repository.find_by_id(saved.questionnaire_id)

        # Then: 문답지가 조회됨
        assert found is not None
        assert found.questionnaire_id == saved.questionnaire_id

    async def test_find_by_id_not_found(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
    ):
        """존재하지 않는 문답지 ID로 조회하면 None을 반환해야 합니다."""
        # Given: 존재하지 않는 문답지 ID
        non_existent_id = Id()

        # When: 조회
        found = await questionnaire_repository.find_by_id(non_existent_id)

        # Then: None 반환
        assert found is None


class TestQuestionnaireRepositoryFindByUserAndCity:
    """QuestionnaireRepository.find_by_user_and_city() 메서드 테스트."""

    async def test_find_by_user_and_city_success(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_questionnaire: Questionnaire,
    ):
        """사용자 ID와 도시 ID로 문답지를 조회할 수 있어야 합니다."""
        # Given: 문답지를 저장
        saved = await questionnaire_repository.save(sample_questionnaire)

        # When: 사용자 ID와 도시 ID로 조회
        found = await questionnaire_repository.find_by_user_and_city(
            saved.user_id, saved.city_id
        )

        # Then: 문답지가 조회됨
        assert found is not None
        assert found.questionnaire_id == saved.questionnaire_id

    async def test_find_by_user_and_city_not_found(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
    ):
        """존재하지 않는 사용자/도시로 조회하면 None을 반환해야 합니다."""
        # Given: 존재하지 않는 사용자 ID와 도시 ID
        non_existent_user_id = Id()
        non_existent_city_id = Id()

        # When: 조회
        found = await questionnaire_repository.find_by_user_and_city(
            non_existent_user_id, non_existent_city_id
        )

        # Then: None 반환
        assert found is None


class TestQuestionnaireRepositoryFindByUserId:
    """QuestionnaireRepository.find_by_user_id() 메서드 테스트."""

    async def test_find_by_user_id_success(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
    ):
        """사용자 ID로 문답지 목록을 조회할 수 있어야 합니다."""
        # Given: 같은 사용자의 문답지 3개 저장
        user_id = Id()
        for i in range(3):
            questionnaire = Questionnaire.create(
                user_id=user_id,
                city_id=Id(),
                question_1_answer=QuestionAnswer(f"답변1-{i+1}"),
                question_2_answer=QuestionAnswer(f"답변2-{i+1}"),
                question_3_answer=QuestionAnswer(f"답변3-{i+1}"),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            await questionnaire_repository.save(questionnaire)

        # When: 사용자 ID로 조회
        questionnaires = await questionnaire_repository.find_by_user_id(user_id)

        # Then: 3개의 문답지가 조회됨 (최신순 정렬)
        assert len(questionnaires) == 3

    async def test_find_by_user_id_with_pagination(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
    ):
        """페이지네이션이 정상 작동해야 합니다."""
        # Given: 같은 사용자의 문답지 5개 저장
        user_id = Id()
        for i in range(5):
            questionnaire = Questionnaire.create(
                user_id=user_id,
                city_id=Id(),
                question_1_answer=QuestionAnswer(f"답변1-{i+1}"),
                question_2_answer=QuestionAnswer(f"답변2-{i+1}"),
                question_3_answer=QuestionAnswer(f"답변3-{i+1}"),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            await questionnaire_repository.save(questionnaire)

        # When: offset=1, limit=2로 조회
        questionnaires = await questionnaire_repository.find_by_user_id(user_id, offset=1, limit=2)

        # Then: 2개의 문답지가 조회됨
        assert len(questionnaires) == 2

    async def test_find_by_user_id_empty(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
    ):
        """문답지가 없는 사용자는 빈 목록을 반환해야 합니다."""
        # Given: 문답지가 없는 사용자
        user_id = Id()

        # When: 조회
        questionnaires = await questionnaire_repository.find_by_user_id(user_id)

        # Then: 빈 목록 반환
        assert questionnaires == []


class TestQuestionnaireRepositoryCountByUserId:
    """QuestionnaireRepository.count_by_user_id() 메서드 테스트."""

    async def test_count_by_user_id(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
    ):
        """사용자의 문답지 개수를 정확히 카운트해야 합니다."""
        # Given: 같은 사용자의 문답지 3개 저장
        user_id = Id()
        for i in range(3):
            questionnaire = Questionnaire.create(
                user_id=user_id,
                city_id=Id(),
                question_1_answer=QuestionAnswer(f"답변1-{i+1}"),
                question_2_answer=QuestionAnswer(f"답변2-{i+1}"),
                question_3_answer=QuestionAnswer(f"답변3-{i+1}"),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            await questionnaire_repository.save(questionnaire)

        # When: 사용자 ID로 카운트
        count = await questionnaire_repository.count_by_user_id(user_id)

        # Then: 3이 반환됨
        assert count == 3

    async def test_count_by_user_id_zero(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
    ):
        """문답지가 없는 사용자는 0을 반환해야 합니다."""
        # Given: 문답지가 없는 사용자
        user_id = Id()

        # When: 카운트
        count = await questionnaire_repository.count_by_user_id(user_id)

        # Then: 0 반환
        assert count == 0
