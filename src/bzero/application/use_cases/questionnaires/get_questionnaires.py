from bzero.application.results.questionnaire_result import QuestionnaireResult
from bzero.domain.services.questionnaire import QuestionnaireService
from bzero.domain.value_objects import Id


class GetQuestionnairesUseCase:
    """문답지 목록 조회 UseCase"""

    def __init__(self, questionnaire_service: QuestionnaireService):
        self._questionnaire_service = questionnaire_service

    async def execute(
        self, user_id: str, offset: int = 0, limit: int = 20
    ) -> tuple[list[QuestionnaireResult], int]:
        """사용자의 문답지 목록을 조회합니다.

        Args:
            user_id: 사용자 ID
            offset: offset
            limit: limit

        Returns:
            (QuestionnaireResult 목록, 전체 개수) 튜플
        """
        questionnaires, total = await self._questionnaire_service.get_questionnaires_by_user(
            user_id=Id(user_id),
            offset=offset,
            limit=limit,
        )
        return [QuestionnaireResult.create_from(q) for q in questionnaires], total
