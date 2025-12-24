from bzero.domain.entities.city_question import CityQuestion
from bzero.domain.errors import NotFoundCityQuestionError
from bzero.domain.repositories.city_question import CityQuestionRepository
from bzero.domain.value_objects import Id


class CityQuestionService:
    """도시 질문 도메인 서비스.

    도시별 질문 조회를 처리합니다.
    관리자용 CRUD는 추후 구현 예정.
    """

    def __init__(
        self,
        city_question_repository: CityQuestionRepository,
    ) -> None:
        """CityQuestionService를 초기화합니다.

        Args:
            city_question_repository: 도시 질문 리포지토리
        """
        self._city_question_repository = city_question_repository

    async def get_question_by_id(self, city_question_id: Id) -> CityQuestion:
        """질문 ID로 조회합니다.

        Args:
            city_question_id: 질문 ID

        Returns:
            질문 엔티티

        Raises:
            NotFoundCityQuestionError: 질문이 존재하지 않을 경우
        """
        question = await self._city_question_repository.find_by_id(city_question_id)
        if question is None:
            raise NotFoundCityQuestionError
        return question

    async def get_active_questions_by_city_id(self, city_id: Id) -> list[CityQuestion]:
        """도시의 활성화된 질문 목록을 조회합니다.

        Args:
            city_id: 도시 ID

        Returns:
            활성화된 질문 목록 (display_order 오름차순)
        """
        return await self._city_question_repository.find_active_by_city_id(city_id)
