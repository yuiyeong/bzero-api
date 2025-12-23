from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.errors import ForbiddenQuestionnaireAccessError
from bzero.domain.services.questionnaire import QuestionnaireService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.user import AuthProvider


class DeleteQuestionnaireUseCase:
    """문답지 삭제 유스케이스.

    문답지를 soft delete 합니다.
    본인이 작성한 문답지만 삭제할 수 있습니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        questionnaire_service: QuestionnaireService,
    ):
        """유스케이스를 초기화합니다.

        Args:
            session: SQLAlchemy 비동기 세션
            user_service: 사용자 도메인 서비스
            questionnaire_service: 문답지 도메인 서비스
        """
        self._session = session
        self._user_service = user_service
        self._questionnaire_service = questionnaire_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
        questionnaire_id: str,
    ) -> None:
        """문답지를 삭제합니다.

        Args:
            provider: 인증 제공자 (예: "supabase")
            provider_user_id: 인증 제공자의 사용자 ID
            questionnaire_id: 삭제할 문답지 ID (hex 문자열)

        Raises:
            NotFoundUserError: 사용자를 찾을 수 없는 경우
            NotFoundQuestionnaireError: 문답지를 찾을 수 없는 경우
            ForbiddenQuestionnaireAccessError: 본인의 문답지가 아닌 경우
        """
        # 1. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        # 2. 문답지 조회
        questionnaire = await self._questionnaire_service.get_questionnaire_by_id(
            questionnaire_id=Id.from_hex(questionnaire_id),
        )

        # 3. 권한 검증 (본인 문답지인지 확인)
        if questionnaire.user_id != user.user_id:
            raise ForbiddenQuestionnaireAccessError

        # 4. 문답지 삭제 (soft delete)
        await self._questionnaire_service.delete_questionnaire(
            questionnaire_id=questionnaire.questionnaire_id,
        )

        # 5. 트랜잭션 커밋
        await self._session.commit()
