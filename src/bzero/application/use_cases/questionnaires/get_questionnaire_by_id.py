from bzero.application.results.questionnaire_result import QuestionnaireResult
from bzero.domain.errors import NotFoundQuestionnaireError
from bzero.domain.services.questionnaire import QuestionnaireService
from bzero.domain.value_objects import Id


class GetQuestionnaireByIdUseCase:
    """문답지 상세 조회 UseCase"""

    def __init__(self, questionnaire_service: QuestionnaireService):
        self._questionnaire_service = questionnaire_service

    async def execute(self, questionnaire_id: str, user_id: str) -> QuestionnaireResult:
        """문답지를 ID로 조회합니다 (본인 확인 포함).

        Args:
            questionnaire_id: 문답지 ID
            user_id: 사용자 ID (소유권 검증용)

        Returns:
            QuestionnaireResult

        Raises:
            NotFoundQuestionnaireError: 문답지를 찾을 수 없거나 소유자가 아닐 때
        """
        questionnaire = await self._questionnaire_service.get_questionnaire_by_id(Id(questionnaire_id))

        # 소유권 검증
        if questionnaire.user_id.value != user_id:
            raise NotFoundQuestionnaireError

        return QuestionnaireResult.create_from(questionnaire)
