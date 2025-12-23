"""SQLAlchemy 기반 CityQuestion Repository.

비동기 리포지토리 구현체입니다.
CityQuestionRepositoryCore의 동기 메서드를 run_sync로 호출합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.city_question import CityQuestion
from bzero.domain.repositories.city_question import CityQuestionRepository
from bzero.domain.value_objects import Id
from bzero.infrastructure.repositories.city_question_core import CityQuestionRepositoryCore


class SqlAlchemyCityQuestionRepository(CityQuestionRepository):
    """SQLAlchemy 기반 CityQuestion Repository (비동기).

    CityQuestionRepositoryCore의 동기 메서드를 run_sync로 호출합니다.
    이 패턴을 통해 로직 중복 없이 비동기 인터페이스를 제공합니다.
    """

    def __init__(self, session: AsyncSession):
        """리포지토리를 초기화합니다.

        Args:
            session: SQLAlchemy AsyncSession 인스턴스
        """
        self._session = session

    async def create(self, city_question: CityQuestion) -> CityQuestion:
        """질문을 생성합니다.

        Args:
            city_question: 생성할 질문 엔티티

        Returns:
            생성된 질문
        """
        return await self._session.run_sync(CityQuestionRepositoryCore.create, city_question)

    async def find_by_id(self, city_question_id: Id) -> CityQuestion | None:
        """ID로 질문을 조회합니다.

        Args:
            city_question_id: 질문 ID

        Returns:
            질문 또는 None
        """
        return await self._session.run_sync(CityQuestionRepositoryCore.find_by_id, city_question_id)

    async def find_active_by_city_id(self, city_id: Id) -> list[CityQuestion]:
        """도시의 활성화된 질문을 조회합니다.

        Args:
            city_id: 도시 ID

        Returns:
            활성화된 질문 목록 (display_order 오름차순)
        """
        return await self._session.run_sync(CityQuestionRepositoryCore.find_active_by_city_id, city_id)

    async def update(self, city_question: CityQuestion) -> CityQuestion:
        """질문을 업데이트합니다.

        Args:
            city_question: 업데이트할 질문 엔티티

        Returns:
            업데이트된 질문

        Raises:
            NotFoundCityQuestionError: 질문을 찾을 수 없는 경우
        """
        return await self._session.run_sync(CityQuestionRepositoryCore.update, city_question)
