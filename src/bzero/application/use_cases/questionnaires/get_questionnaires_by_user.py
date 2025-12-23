from bzero.application.results.common import PaginatedResult
from bzero.application.results.questionnaire_result import QuestionnaireResult
from bzero.domain.services.questionnaire import QuestionnaireService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects.user import AuthProvider


class GetQuestionnairesByUserUseCase:
    """사용자 문답지 목록 조회 유스케이스.

    사용자가 작성한 문답지 목록을 페이지네이션하여 조회합니다.
    """

    def __init__(
        self,
        user_service: UserService,
        questionnaire_service: QuestionnaireService,
    ):
        """유스케이스를 초기화합니다.

        Args:
            user_service: 사용자 도메인 서비스
            questionnaire_service: 문답지 도메인 서비스
        """
        self._user_service = user_service
        self._questionnaire_service = questionnaire_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> PaginatedResult[QuestionnaireResult]:
        """사용자의 문답지 목록을 조회합니다.

        Args:
            provider: 인증 제공자 (예: "supabase")
            provider_user_id: 인증 제공자의 사용자 ID
            limit: 조회할 최대 개수 (기본값: 20)
            offset: 건너뛸 개수 (기본값: 0)

        Returns:
            페이지네이션된 문답지 목록

        Raises:
            NotFoundUserError: 사용자를 찾을 수 없는 경우
        """
        # 1. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        # 2. 문답지 목록 및 총 개수 조회
        questionnaires, total = await self._questionnaire_service.get_questionnaires_by_user_id(
            user_id=user.user_id,
            limit=limit,
            offset=offset,
        )

        # 3. 결과 변환
        items = [QuestionnaireResult.create_from(q) for q in questionnaires]

        return PaginatedResult(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )
