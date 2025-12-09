from datetime import datetime
from zoneinfo import ZoneInfo

from bzero.domain.entities.questionnaire import Questionnaire
from bzero.domain.errors import DuplicatedQuestionnaireError, NotFoundQuestionnaireError
from bzero.domain.repositories.questionnaire import QuestionnaireRepository
from bzero.domain.value_objects import Id, QuestionAnswer


class QuestionnaireService:
    """문답지 도메인 서비스

    Questionnaire 생성/조회를 담당합니다.
    주의: 모든 메서드는 데이터베이스 트랜잭션 내에서 호출되어야 합니다.
    """

    def __init__(self, questionnaire_repository: QuestionnaireRepository, timezone: ZoneInfo):
        self._questionnaire_repository = questionnaire_repository
        self._timezone = timezone

    async def create_questionnaire(
        self,
        user_id: Id,
        city_id: Id,
        question_1_answer: QuestionAnswer,
        question_2_answer: QuestionAnswer,
        question_3_answer: QuestionAnswer,
    ) -> Questionnaire:
        """문답지를 생성합니다.

        Args:
            user_id: 사용자 ID
            city_id: 도시 ID
            question_1_answer: 질문 1 답변
            question_2_answer: 질문 2 답변
            question_3_answer: 질문 3 답변

        Returns:
            생성된 Questionnaire 엔티티

        Raises:
            DuplicatedQuestionnaireError: 같은 도시에 이미 문답지가 존재할 때
        """
        # 중복 확인
        existing = await self._questionnaire_repository.find_by_user_and_city(user_id, city_id)
        if existing:
            raise DuplicatedQuestionnaireError

        # 문답지 생성
        now = datetime.now(self._timezone)
        questionnaire = Questionnaire.create(
            user_id=user_id,
            city_id=city_id,
            question_1_answer=question_1_answer,
            question_2_answer=question_2_answer,
            question_3_answer=question_3_answer,
            created_at=now,
            updated_at=now,
        )

        # 저장
        return await self._questionnaire_repository.save(questionnaire)

    async def get_questionnaire_by_id(self, questionnaire_id: Id) -> Questionnaire:
        """문답지를 ID로 조회합니다.

        Args:
            questionnaire_id: 문답지 ID

        Returns:
            Questionnaire 엔티티

        Raises:
            NotFoundQuestionnaireError: 문답지를 찾을 수 없을 때
        """
        questionnaire = await self._questionnaire_repository.find_by_id(questionnaire_id)
        if not questionnaire:
            raise NotFoundQuestionnaireError
        return questionnaire

    async def get_questionnaire_by_user_and_city(self, user_id: Id, city_id: Id) -> Questionnaire | None:
        """사용자 ID와 도시 ID로 문답지를 조회합니다.

        Args:
            user_id: 사용자 ID
            city_id: 도시 ID

        Returns:
            Questionnaire 엔티티 또는 None
        """
        return await self._questionnaire_repository.find_by_user_and_city(user_id, city_id)

    async def get_questionnaires_by_user(
        self, user_id: Id, offset: int = 0, limit: int = 20
    ) -> tuple[list[Questionnaire], int]:
        """사용자의 문답지 목록을 조회합니다.

        Args:
            user_id: 사용자 ID
            offset: offset
            limit: limit

        Returns:
            (문답지 목록, 전체 개수) 튜플
        """
        questionnaires = await self._questionnaire_repository.find_by_user_id(user_id, offset, limit)
        total = await self._questionnaire_repository.count_by_user_id(user_id)
        return questionnaires, total

    async def mark_points_earned(self, questionnaire: Questionnaire) -> Questionnaire:
        """문답지에 포인트 지급 완료 표시를 합니다.

        Args:
            questionnaire: Questionnaire 엔티티

        Returns:
            업데이트된 Questionnaire 엔티티
        """
        questionnaire.mark_points_earned()
        questionnaire.updated_at = datetime.now(self._timezone)
        return await self._questionnaire_repository.save(questionnaire)
