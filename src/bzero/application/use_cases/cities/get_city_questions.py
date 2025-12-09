from bzero.domain.services.city_question import CityQuestionService
from bzero.domain.value_objects import Id


class GetCityQuestionsUseCase:
    """도시별 질문 조회 UseCase"""

    def __init__(self, city_question_service: CityQuestionService):
        self._city_question_service = city_question_service

    async def execute(self, city_id: str) -> list[str]:
        """도시별 질문 3개를 조회합니다.

        Args:
            city_id: 도시 ID

        Returns:
            질문 3개 리스트

        Raises:
            CityNotFoundError: 존재하지 않는 도시 ID인 경우
        """
        return await self._city_question_service.get_questions_by_city(Id(city_id))
