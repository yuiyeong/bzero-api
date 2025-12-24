from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.questionnaire_result import QuestionnaireResult
from bzero.domain.errors import NotFoundRoomStayError
from bzero.domain.services.city_question import CityQuestionService
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.services.questionnaire import QuestionnaireService
from bzero.domain.services.room_stay import RoomStayService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.point_transaction import (
    TransactionReason,
    TransactionReference,
)
from bzero.domain.value_objects.user import AuthProvider


class CreateQuestionnaireUseCase:
    """문답지 생성 유스케이스.

    체류 중 도시 질문에 답변하고 포인트를 지급합니다.

    비즈니스 규칙:
        - 현재 활성 체류(CHECKED_IN 또는 EXTENDED) 중일 때만 작성 가능
        - 체류당 질문당 1개의 답변만 작성 가능 (1문 1답)
        - 최초 작성 시 50P 지급 (TransactionReference.QUESTIONNAIRES로 중복 방지)
    """

    QUESTIONNAIRE_REWARD_POINTS = 50

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        room_stay_service: RoomStayService,
        city_question_service: CityQuestionService,
        questionnaire_service: QuestionnaireService,
        point_transaction_service: PointTransactionService,
    ):
        """유스케이스를 초기화합니다.

        Args:
            session: SQLAlchemy 비동기 세션
            user_service: 사용자 도메인 서비스
            room_stay_service: 체류 도메인 서비스
            city_question_service: 도시 질문 도메인 서비스
            questionnaire_service: 문답지 도메인 서비스
            point_transaction_service: 포인트 거래 도메인 서비스
        """
        self._session = session
        self._user_service = user_service
        self._room_stay_service = room_stay_service
        self._city_question_service = city_question_service
        self._questionnaire_service = questionnaire_service
        self._point_transaction_service = point_transaction_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
        city_question_id: str,
        answer_text: str,
    ) -> QuestionnaireResult:
        """문답지를 생성합니다.

        Args:
            provider: 인증 제공자 (예: "supabase")
            provider_user_id: 인증 제공자의 사용자 ID
            city_question_id: 질문 ID
            answer_text: 답변 내용 (1-200자)

        Returns:
            생성된 문답지 정보

        Raises:
            NotFoundUserError: 사용자를 찾을 수 없는 경우
            NotFoundRoomStayError: 활성 체류가 없는 경우
            NotFoundCityQuestionError: 질문을 찾을 수 없는 경우
            DuplicatedQuestionnaireError: 이미 해당 질문에 답변이 있는 경우
            InvalidQuestionnaireAnswerError: 답변이 유효하지 않은 경우
        """
        # 1. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        # 2. 현재 활성 체류 조회 (없으면 에러)
        room_stay = await self._room_stay_service.get_checked_in_by_user_id(user.user_id)
        if room_stay is None:
            raise NotFoundRoomStayError

        # 3. 질문 조회 (존재 여부 확인)
        question = await self._city_question_service.get_question_by_id(
            city_question_id=Id.from_hex(city_question_id),
        )

        # 4. 문답지 생성 (중복 체크 포함)
        questionnaire = await self._questionnaire_service.create_questionnaire(
            room_stay=room_stay,
            city_question=question,
            answer=answer_text,
        )

        # 5. 포인트 지급 (TransactionReference.QUESTIONNAIRES로 중복 방지)
        await self._point_transaction_service.earn_by(
            user=user,
            amount=self.QUESTIONNAIRE_REWARD_POINTS,
            reason=TransactionReason.QUESTIONNAIRE,
            reference_type=TransactionReference.QUESTIONNAIRES,
            reference_id=questionnaire.questionnaire_id,
        )

        # 6. 트랜잭션 커밋
        await self._session.commit()

        return QuestionnaireResult.create_from(questionnaire)
