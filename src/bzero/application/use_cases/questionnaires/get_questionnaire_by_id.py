from bzero.application.results.questionnaire_result import QuestionnaireResult
from bzero.domain.errors import ForbiddenQuestionnaireError
from bzero.domain.services.questionnaire import QuestionnaireService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import AuthProvider, Id


class GetQuestionnaireByIdUseCase:
    """문답지 상세 조회 UseCase"""

    def __init__(self, user_service: UserService, questionnaire_service: QuestionnaireService):
        self._user_service = user_service
        self._questionnaire_service = questionnaire_service

    async def execute(self, questionnaire_id: str, provider: str, provider_user_id: str) -> QuestionnaireResult:
        """문답지를 ID로 조회합니다 (본인 확인 포함).

        Args:
            questionnaire_id: 문답지 ID
            provider: 인증 제공자
            provider_user_id: 제공자의 user_id

        Returns:
            QuestionnaireResult

        Raises:
            NotFoundQuestionnaireError: 문답지를 찾을 수 없을 때
            ForbiddenQuestionnaireError: 문답지 소유자가 아닐 때
        """
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        questionnaire = await self._questionnaire_service.get_questionnaire_by_id(Id.from_hex(questionnaire_id))

        # 소유권 검증
        if questionnaire.user_id != user.user_id:
            raise ForbiddenQuestionnaireError

        return QuestionnaireResult.create_from(questionnaire)
