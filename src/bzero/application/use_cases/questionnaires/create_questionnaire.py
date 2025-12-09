from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.questionnaire_result import QuestionnaireResult
from bzero.domain.errors import DuplicatedQuestionnaireError
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.services.questionnaire import QuestionnaireService
from bzero.domain.value_objects import Id, QuestionAnswer, TransactionReason, TransactionReference


class CreateQuestionnaireUseCase:
    """문답지 작성 UseCase

    - 중복 작성 방지 (같은 도시에 이미 문답지가 있으면 실패)
    - 문답지 저장 후 포인트 지급 (50P, 도시별 1회)
    """

    QUESTIONNAIRE_POINTS = 50

    def __init__(
        self,
        session: AsyncSession,
        questionnaire_service: QuestionnaireService,
        point_transaction_service: PointTransactionService,
    ):
        self._session = session
        self._questionnaire_service = questionnaire_service
        self._point_transaction_service = point_transaction_service

    async def execute(
        self,
        user_id: str,
        city_id: str,
        question_1_answer: str,
        question_2_answer: str,
        question_3_answer: str,
    ) -> QuestionnaireResult:
        """문답지를 작성합니다.

        Args:
            user_id: 사용자 ID
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
            # 1. 문답지 생성
            questionnaire = await self._questionnaire_service.create_questionnaire(
                user_id=Id(user_id),
                city_id=Id(city_id),
                question_1_answer=QuestionAnswer(question_1_answer),
                question_2_answer=QuestionAnswer(question_2_answer),
                question_3_answer=QuestionAnswer(question_3_answer),
            )

            # 2. 포인트 지급 (50P, 도시별 1회)
            await self._point_transaction_service.earn_points(
                user_id=Id(user_id),
                amount=self.QUESTIONNAIRE_POINTS,
                reason=TransactionReason.QUESTIONNAIRE,
                reference_type=TransactionReference.QUESTIONNAIRES,
                reference_id=questionnaire.questionnaire_id,
                description=f"문답지 작성 보상 (도시: {city_id})",
            )

            # 3. 포인트 지급 완료 표시
            questionnaire = await self._questionnaire_service.mark_points_earned(questionnaire)

            await self._session.commit()
            return QuestionnaireResult.create_from(questionnaire)

        except Exception:
            await self._session.rollback()
            raise
