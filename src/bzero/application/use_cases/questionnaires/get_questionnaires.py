from bzero.application.results.common import PaginatedResult
from bzero.application.results.questionnaire_result import QuestionnaireResult
from bzero.domain.services.questionnaire import QuestionnaireService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import AuthProvider


class GetQuestionnairesUseCase:
    """문답지 목록 조회 UseCase"""

    def __init__(self, user_service: UserService, questionnaire_service: QuestionnaireService):
        self._user_service = user_service
        self._questionnaire_service = questionnaire_service

    async def execute(self, provider: str, provider_user_id: str, offset: int = 0, limit: int = 20) -> PaginatedResult[QuestionnaireResult]:
        """사용자의 문답지 목록을 조회합니다.

        Args:
            provider: 인증 제공자
            provider_user_id: 제공자의 user_id
            offset: offset
            limit: limit

        Returns:
            PaginatedResult[QuestionnaireResult]
        """
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        questionnaires, total = await self._questionnaire_service.get_questionnaires_by_user(
            user_id=user.user_id,
            offset=offset,
            limit=limit,
        )
        return PaginatedResult(
            items=[QuestionnaireResult.create_from(q) for q in questionnaires],
            total=total,
            offset=offset,
            limit=limit,
        )
