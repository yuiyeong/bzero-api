"""QuestionnaireService 단위 테스트."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest
from uuid_utils import uuid7

from bzero.domain.entities.city_question import CityQuestion
from bzero.domain.entities.questionnaire import Questionnaire
from bzero.domain.entities.room_stay import RoomStay
from bzero.domain.errors import DuplicatedQuestionnaireError, NotFoundQuestionnaireError
from bzero.domain.repositories.questionnaire import QuestionnaireRepository
from bzero.domain.services.questionnaire import QuestionnaireService
from bzero.domain.value_objects import Id


@pytest.fixture
def mock_questionnaire_repository() -> MagicMock:
    """Mock QuestionnaireRepository."""
    return MagicMock(spec=QuestionnaireRepository)


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone."""
    return ZoneInfo("Asia/Seoul")


@pytest.fixture
def questionnaire_service(
    mock_questionnaire_repository: MagicMock,
    timezone: ZoneInfo,
) -> QuestionnaireService:
    """QuestionnaireService with mocked repository."""
    return QuestionnaireService(mock_questionnaire_repository, timezone)


@pytest.fixture
def sample_room_stay(timezone: ZoneInfo) -> RoomStay:
    """샘플 체류 엔티티."""
    now = datetime.now(timezone)
    return RoomStay.create(
        user_id=Id(uuid7()),
        city_id=Id(uuid7()),
        guest_house_id=Id(uuid7()),
        room_id=Id(uuid7()),
        ticket_id=Id(uuid7()),
        check_in_at=now,
        scheduled_check_out_at=now + timedelta(hours=24),
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_city_question(timezone: ZoneInfo) -> CityQuestion:
    """샘플 도시 질문 엔티티."""
    now = datetime.now(timezone)
    return CityQuestion.create(
        city_id=Id(uuid7()),
        question="오늘 가장 감사했던 순간은 언제인가요?",
        display_order=1,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_questionnaire(
    timezone: ZoneInfo,
    sample_room_stay: RoomStay,
    sample_city_question: CityQuestion,
) -> Questionnaire:
    """샘플 문답지."""
    now = datetime.now(timezone)
    return Questionnaire.create(
        user_id=sample_room_stay.user_id,
        room_stay_id=sample_room_stay.room_stay_id,
        city_question_id=sample_city_question.city_question_id,
        city_question=sample_city_question.question,
        answer="오늘 아침에 친구가 커피를 사줬어요.",
        city_id=sample_room_stay.city_id,
        guest_house_id=sample_room_stay.guest_house_id,
        created_at=now,
        updated_at=now,
    )


class TestQuestionnaireServiceCreateQuestionnaire:
    """create_questionnaire 메서드 테스트."""

    async def test_create_questionnaire_success(
        self,
        questionnaire_service: QuestionnaireService,
        mock_questionnaire_repository: MagicMock,
        sample_room_stay: RoomStay,
        sample_city_question: CityQuestion,
    ):
        """문답지를 성공적으로 생성할 수 있다."""
        # Given
        answer = "오늘 아침에 친구가 커피를 사줬어요."

        mock_questionnaire_repository.exists_by_room_stay_and_question = AsyncMock(return_value=False)

        async def mock_create(questionnaire: Questionnaire) -> Questionnaire:
            return questionnaire

        mock_questionnaire_repository.create = AsyncMock(side_effect=mock_create)

        # When
        questionnaire = await questionnaire_service.create_questionnaire(
            room_stay=sample_room_stay,
            city_question=sample_city_question,
            answer=answer,
        )

        # Then
        assert questionnaire.user_id == sample_room_stay.user_id
        assert questionnaire.room_stay_id == sample_room_stay.room_stay_id
        assert questionnaire.city_question_id == sample_city_question.city_question_id
        assert questionnaire.city_question == sample_city_question.question
        assert questionnaire.answer == answer
        assert questionnaire.city_id == sample_room_stay.city_id
        assert questionnaire.guest_house_id == sample_room_stay.guest_house_id
        mock_questionnaire_repository.exists_by_room_stay_and_question.assert_called_once_with(
            room_stay_id=sample_room_stay.room_stay_id,
            city_question_id=sample_city_question.city_question_id,
        )
        mock_questionnaire_repository.create.assert_called_once()

    async def test_create_questionnaire_raises_error_when_already_exists(
        self,
        questionnaire_service: QuestionnaireService,
        mock_questionnaire_repository: MagicMock,
        sample_room_stay: RoomStay,
        sample_city_question: CityQuestion,
    ):
        """이미 해당 체류에서 해당 질문에 답변이 존재하면 에러가 발생한다."""
        # Given
        answer = "답변입니다."

        mock_questionnaire_repository.exists_by_room_stay_and_question = AsyncMock(return_value=True)

        # When/Then
        with pytest.raises(DuplicatedQuestionnaireError):
            await questionnaire_service.create_questionnaire(
                room_stay=sample_room_stay,
                city_question=sample_city_question,
                answer=answer,
            )


class TestQuestionnaireServiceGetQuestionnaireById:
    """get_questionnaire_by_id 메서드 테스트."""

    async def test_get_questionnaire_by_id_success(
        self,
        questionnaire_service: QuestionnaireService,
        mock_questionnaire_repository: MagicMock,
        sample_questionnaire: Questionnaire,
    ):
        """문답지 ID로 문답지를 조회할 수 있다."""
        # Given
        mock_questionnaire_repository.find_by_id = AsyncMock(return_value=sample_questionnaire)

        # When
        questionnaire = await questionnaire_service.get_questionnaire_by_id(sample_questionnaire.questionnaire_id)

        # Then
        assert questionnaire.questionnaire_id == sample_questionnaire.questionnaire_id
        mock_questionnaire_repository.find_by_id.assert_called_once_with(sample_questionnaire.questionnaire_id)

    async def test_get_questionnaire_by_id_raises_error_when_not_found(
        self,
        questionnaire_service: QuestionnaireService,
        mock_questionnaire_repository: MagicMock,
    ):
        """문답지를 찾을 수 없으면 에러가 발생한다."""
        # Given
        questionnaire_id = Id(uuid7())
        mock_questionnaire_repository.find_by_id = AsyncMock(return_value=None)

        # When/Then
        with pytest.raises(NotFoundQuestionnaireError):
            await questionnaire_service.get_questionnaire_by_id(questionnaire_id)


class TestQuestionnaireServiceGetQuestionnairesByUserId:
    """get_questionnaires_by_user_id 메서드 테스트."""

    async def test_get_questionnaires_by_user_id_success(
        self,
        questionnaire_service: QuestionnaireService,
        mock_questionnaire_repository: MagicMock,
        sample_questionnaire: Questionnaire,
    ):
        """사용자의 모든 문답지를 조회할 수 있다."""
        # Given
        mock_questionnaire_repository.find_all_by_user_id = AsyncMock(return_value=[sample_questionnaire])
        mock_questionnaire_repository.count_by_user_id = AsyncMock(return_value=1)

        # When
        questionnaires, total = await questionnaire_service.get_questionnaires_by_user_id(sample_questionnaire.user_id)

        # Then
        assert len(questionnaires) == 1
        assert total == 1
        assert questionnaires[0].user_id == sample_questionnaire.user_id
        mock_questionnaire_repository.find_all_by_user_id.assert_called_once_with(
            user_id=sample_questionnaire.user_id, limit=20, offset=0
        )
        mock_questionnaire_repository.count_by_user_id.assert_called_once_with(sample_questionnaire.user_id)

    async def test_get_questionnaires_by_user_id_with_pagination(
        self,
        questionnaire_service: QuestionnaireService,
        mock_questionnaire_repository: MagicMock,
    ):
        """pagination 파라미터로 문답지 목록을 조회할 수 있다."""
        # Given
        user_id = Id(uuid7())
        mock_questionnaire_repository.find_all_by_user_id = AsyncMock(return_value=[])
        mock_questionnaire_repository.count_by_user_id = AsyncMock(return_value=50)

        # When
        questionnaires, total = await questionnaire_service.get_questionnaires_by_user_id(
            user_id=user_id, limit=10, offset=20
        )

        # Then
        assert len(questionnaires) == 0
        assert total == 50
        mock_questionnaire_repository.find_all_by_user_id.assert_called_once_with(user_id=user_id, limit=10, offset=20)

    async def test_get_questionnaires_by_user_id_returns_empty_list(
        self,
        questionnaire_service: QuestionnaireService,
        mock_questionnaire_repository: MagicMock,
    ):
        """문답지가 없으면 빈 리스트를 반환한다."""
        # Given
        user_id = Id(uuid7())
        mock_questionnaire_repository.find_all_by_user_id = AsyncMock(return_value=[])
        mock_questionnaire_repository.count_by_user_id = AsyncMock(return_value=0)

        # When
        questionnaires, total = await questionnaire_service.get_questionnaires_by_user_id(user_id)

        # Then
        assert questionnaires == []
        assert total == 0


class TestQuestionnaireServiceGetQuestionnairesByRoomStayId:
    """get_questionnaires_by_room_stay_id 메서드 테스트."""

    async def test_get_questionnaires_by_room_stay_id_success(
        self,
        questionnaire_service: QuestionnaireService,
        mock_questionnaire_repository: MagicMock,
        sample_questionnaire: Questionnaire,
    ):
        """체류 ID로 문답지 목록을 조회할 수 있다."""
        # Given
        mock_questionnaire_repository.find_all_by_room_stay_id = AsyncMock(return_value=[sample_questionnaire])

        # When
        questionnaires = await questionnaire_service.get_questionnaires_by_room_stay_id(
            sample_questionnaire.room_stay_id
        )

        # Then
        assert len(questionnaires) == 1
        assert questionnaires[0].room_stay_id == sample_questionnaire.room_stay_id
        mock_questionnaire_repository.find_all_by_room_stay_id.assert_called_once_with(
            sample_questionnaire.room_stay_id
        )

    async def test_get_questionnaires_by_room_stay_id_returns_empty_list(
        self,
        questionnaire_service: QuestionnaireService,
        mock_questionnaire_repository: MagicMock,
    ):
        """문답지가 없으면 빈 리스트를 반환한다."""
        # Given
        room_stay_id = Id(uuid7())
        mock_questionnaire_repository.find_all_by_room_stay_id = AsyncMock(return_value=[])

        # When
        questionnaires = await questionnaire_service.get_questionnaires_by_room_stay_id(room_stay_id)

        # Then
        assert questionnaires == []


class TestQuestionnaireServiceUpdateQuestionnaire:
    """update_questionnaire 메서드 테스트."""

    async def test_update_questionnaire_success(
        self,
        questionnaire_service: QuestionnaireService,
        mock_questionnaire_repository: MagicMock,
        sample_questionnaire: Questionnaire,
    ):
        """문답지를 성공적으로 수정할 수 있다."""
        # Given
        new_answer = "수정된 답변입니다."
        mock_questionnaire_repository.find_by_id = AsyncMock(return_value=sample_questionnaire)
        mock_questionnaire_repository.update = AsyncMock(return_value=sample_questionnaire)

        # When
        updated_questionnaire = await questionnaire_service.update_questionnaire(
            questionnaire_id=sample_questionnaire.questionnaire_id,
            answer_text=new_answer,
        )

        # Then
        assert updated_questionnaire.answer == new_answer
        mock_questionnaire_repository.find_by_id.assert_called_once_with(sample_questionnaire.questionnaire_id)
        mock_questionnaire_repository.update.assert_called_once()

    async def test_update_questionnaire_raises_error_when_not_found(
        self,
        questionnaire_service: QuestionnaireService,
        mock_questionnaire_repository: MagicMock,
    ):
        """문답지를 찾을 수 없으면 에러가 발생한다."""
        # Given
        questionnaire_id = Id(uuid7())
        new_answer = "수정된 답변입니다."
        mock_questionnaire_repository.find_by_id = AsyncMock(return_value=None)

        # When/Then
        with pytest.raises(NotFoundQuestionnaireError):
            await questionnaire_service.update_questionnaire(
                questionnaire_id=questionnaire_id,
                answer_text=new_answer,
            )


class TestQuestionnaireServiceDeleteQuestionnaire:
    """delete_questionnaire 메서드 테스트."""

    async def test_delete_questionnaire_success(
        self,
        questionnaire_service: QuestionnaireService,
        mock_questionnaire_repository: MagicMock,
        sample_questionnaire: Questionnaire,
    ):
        """문답지를 성공적으로 삭제할 수 있다 (soft delete)."""
        # Given
        mock_questionnaire_repository.find_by_id = AsyncMock(return_value=sample_questionnaire)
        mock_questionnaire_repository.update = AsyncMock(return_value=sample_questionnaire)

        # When
        deleted_questionnaire = await questionnaire_service.delete_questionnaire(sample_questionnaire.questionnaire_id)

        # Then
        assert deleted_questionnaire.deleted_at is not None
        mock_questionnaire_repository.find_by_id.assert_called_once_with(sample_questionnaire.questionnaire_id)
        mock_questionnaire_repository.update.assert_called_once()

    async def test_delete_questionnaire_raises_error_when_not_found(
        self,
        questionnaire_service: QuestionnaireService,
        mock_questionnaire_repository: MagicMock,
    ):
        """문답지를 찾을 수 없으면 에러가 발생한다."""
        # Given
        questionnaire_id = Id(uuid7())
        mock_questionnaire_repository.find_by_id = AsyncMock(return_value=None)

        # When/Then
        with pytest.raises(NotFoundQuestionnaireError):
            await questionnaire_service.delete_questionnaire(questionnaire_id)
