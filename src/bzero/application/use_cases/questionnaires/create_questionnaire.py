from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.questionnaire_result import QuestionnaireResult
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.services.questionnaire import QuestionnaireService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import AuthProvider, Id, QuestionAnswer, TransactionReason, TransactionReference


class CreateQuestionnaireUseCase:
    """문답지 작성 UseCase

    - 중복 작성 방지 (같은 도시에 이미 문답지가 있으면 실패)
    - 문답지 저장 후 포인트 지급 (50P, 도시별 1회)
    """

    QUESTIONNAIRE_POINTS = 50

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        questionnaire_service: QuestionnaireService,
        point_transaction_service: PointTransactionService,
    ):
        self._session = session
        self._user_service = user_service
        self._questionnaire_service = questionnaire_service
        self._point_transaction_service = point_transaction_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
        city_id: str,
        question_1_answer: str,
        question_2_answer: str,
        question_3_answer: str,
    ) -> QuestionnaireResult:
        """문답지를 작성합니다.

        Args:
            provider: 인증 제공자
            provider_user_id: 제공자의 user_id
            city_id: 도시 ID
            question_1_answer: 질문 1 답변
            question_2_answer: 질문 2 답변
            question_3_answer: 질문 3 답변

        Returns:
            QuestionnaireResult

        Raises:
            DuplicatedQuestionnaireError: 같은 도시에 이미 문답지가 존재할 때
        """
        try:
            # 0. 사용자 조회
            user = await self._user_service.find_user_by_provider_and_provider_user_id(
                provider=AuthProvider(provider),
                provider_user_id=provider_user_id,
            )
            # 1. 문답지 생성
            questionnaire = await self._questionnaire_service.create_questionnaire(
                user_id=user.user_id,
                city_id=Id.from_hex(city_id),
                question_1_answer=QuestionAnswer(question_1_answer),
                question_2_answer=QuestionAnswer(question_2_answer),
                question_3_answer=QuestionAnswer(question_3_answer),
            )

            # 2. 포인트 지급 (50P, 도시별 1회)
            _, _ = await self._point_transaction_service.earn_by(
                user=user,
                amount=self.QUESTIONNAIRE_POINTS,
                reason=TransactionReason.QUESTIONNAIRE,
                reference_type=TransactionReference.QUESTIONNAIRES,
                reference_id=questionnaire.questionnaire_id,
                description=f"문답지 작성 보상 (도시: {city_id})",
            )

            # 3. 포인트 지급 완료 표시
            questionnaire.mark_points_earned()

            await self._session.commit()
            return QuestionnaireResult.create_from(questionnaire)

        except Exception:
            await self._session.rollback()
            raise
