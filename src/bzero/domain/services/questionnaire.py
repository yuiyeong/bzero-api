from datetime import datetime
from zoneinfo import ZoneInfo

from bzero.domain.entities import RoomStay
from bzero.domain.entities.city_question import CityQuestion
from bzero.domain.entities.questionnaire import Questionnaire
from bzero.domain.errors import (
    DuplicatedQuestionnaireError,
    NotFoundQuestionnaireError,
)
from bzero.domain.repositories.questionnaire import QuestionnaireRepository
from bzero.domain.value_objects import Id


class QuestionnaireService:
    """문답지 도메인 서비스.

    문답지 CRUD 및 비즈니스 로직을 처리합니다.
    포인트 지급은 유스케이스에서 PointTransactionService를 통해 처리합니다.
    """

    def __init__(
        self,
        questionnaire_repository: QuestionnaireRepository,
        timezone: ZoneInfo,
    ) -> None:
        """QuestionnaireService를 초기화합니다.

        Args:
            questionnaire_repository: 문답지 리포지토리
            timezone: 시간대 정보
        """
        self._questionnaire_repository = questionnaire_repository
        self._timezone = timezone

    async def create_questionnaire(
        self,
        room_stay: RoomStay,
        city_question: CityQuestion,
        answer: str,
    ) -> Questionnaire:
        """새 문답지를 생성합니다.

        Raises:
            DuplicatedQuestionnaireError: 해당 체류에서 해당 질문에 이미 답변이 존재할 경우
        """
        if await self._questionnaire_repository.exists_by_room_stay_and_question(
            room_stay_id=room_stay.room_stay_id,
            city_question_id=city_question.city_question_id,
        ):
            raise DuplicatedQuestionnaireError

        now = datetime.now(self._timezone)
        questionnaire = Questionnaire.create(
            user_id=room_stay.user_id,
            room_stay_id=room_stay.room_stay_id,
            city_question_id=city_question.city_question_id,
            city_question=city_question.question,
            answer=answer,
            city_id=room_stay.city_id,
            guest_house_id=room_stay.guest_house_id,
            created_at=now,
            updated_at=now,
        )

        return await self._questionnaire_repository.create(questionnaire)

    async def get_questionnaire_by_id(self, questionnaire_id: Id) -> Questionnaire:
        """문답지 ID로 조회합니다.

        Args:
            questionnaire_id: 문답지 ID

        Returns:
            문답지 엔티티

        Raises:
            NotFoundQuestionnaireError: 문답지가 존재하지 않을 경우
        """
        questionnaire = await self._questionnaire_repository.find_by_id(questionnaire_id)
        if questionnaire is None:
            raise NotFoundQuestionnaireError
        return questionnaire

    async def get_questionnaires_by_user_id(
        self,
        user_id: Id,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Questionnaire], int]:
        """사용자의 문답지 목록을 페이지네이션으로 조회합니다.

        Args:
            user_id: 사용자 ID
            limit: 조회 개수
            offset: 오프셋

        Returns:
            (문답지 목록, 전체 개수) 튜플
        """
        questionnaires = await self._questionnaire_repository.find_all_by_user_id(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
        total = await self._questionnaire_repository.count_by_user_id(user_id)
        return questionnaires, total

    async def get_questionnaires_by_room_stay_id(
        self,
        room_stay_id: Id,
    ) -> list[Questionnaire]:
        """체류 ID로 문답지 목록을 조회합니다.

        Args:
            room_stay_id: 체류 ID

        Returns:
            문답지 목록
        """
        return await self._questionnaire_repository.find_all_by_room_stay_id(room_stay_id)

    async def update_questionnaire(
        self,
        questionnaire_id: Id,
        answer_text: str,
    ) -> Questionnaire:
        """문답지를 수정합니다.

        Args:
            questionnaire_id: 문답지 ID
            answer_text: 새 답변 내용

        Returns:
            수정된 문답지 엔티티

        Raises:
            NotFoundQuestionnaireError: 문답지가 존재하지 않을 경우
        """
        questionnaire = await self.get_questionnaire_by_id(questionnaire_id)
        now = datetime.now(self._timezone)
        questionnaire.update_answer(
            answer_text=answer_text,
            updated_at=now,
        )
        return await self._questionnaire_repository.update(questionnaire)

    async def delete_questionnaire(self, questionnaire_id: Id) -> Questionnaire:
        """문답지를 삭제합니다 (soft delete).

        Args:
            questionnaire_id: 문답지 ID

        Returns:
            삭제된 문답지 엔티티

        Raises:
            NotFoundQuestionnaireError: 문답지가 존재하지 않을 경우
        """
        questionnaire = await self.get_questionnaire_by_id(questionnaire_id)
        now = datetime.now(self._timezone)
        questionnaire.soft_delete(deleted_at=now)
        return await self._questionnaire_repository.update(questionnaire)
