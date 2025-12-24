from bzero.application.results import PaginatedResult
from bzero.application.results.city_question_result import CityQuestionResult
from bzero.domain.services.city_question import CityQuestionService
from bzero.domain.value_objects import Id


class GetCityQuestionsUseCase:
    """도시별 질문 목록 조회 유스케이스.

    도시의 활성화된 질문 목록을 display_order 순으로 조회합니다.
    """

    def __init__(
        self,
        city_question_service: CityQuestionService,
    ):
        """유스케이스를 초기화합니다.

        Args:
            city_question_service: 도시 질문 도메인 서비스
        """
        self._city_question_service = city_question_service

    async def execute(
        self,
        city_id: str,
    ) -> PaginatedResult[CityQuestionResult]:
        """도시의 활성화된 질문 목록을 조회합니다.

        Args:
            city_id: 도시 ID

        Returns:
            활성화된 질문 목록 (display_order 순)
        """
        questions = await self._city_question_service.get_active_questions_by_city_id(
            city_id=Id.from_hex(city_id),
        )

        return PaginatedResult(
            items=[CityQuestionResult.create_from(question) for question in questions],
            total=len(questions),
            offset=0,
            limit=len(questions),
        )
