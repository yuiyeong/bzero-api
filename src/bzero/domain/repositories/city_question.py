from abc import ABC, abstractmethod

from bzero.domain.entities.city_question import CityQuestion
from bzero.domain.value_objects import Id


class CityQuestionRepository(ABC):
    """도시 질문 리포지토리 인터페이스 (비동기)."""

    @abstractmethod
    async def create(self, city_question: CityQuestion) -> CityQuestion:
        """도시 질문을 생성합니다.

        Args:
            city_question: 생성할 질문 엔티티

        Returns:
            생성된 질문 엔티티
        """

    @abstractmethod
    async def find_by_id(self, city_question_id: Id) -> CityQuestion | None:
        """질문 ID로 조회합니다.

        Args:
            city_question_id: 질문 ID

        Returns:
            질문 엔티티 또는 None
        """

    @abstractmethod
    async def find_active_by_city_id(self, city_id: Id) -> list[CityQuestion]:
        """도시의 활성화된 질문 목록을 조회합니다.

        display_order 오름차순으로 정렬됩니다.

        Args:
            city_id: 도시 ID

        Returns:
            활성화된 질문 목록
        """

    @abstractmethod
    async def update(self, city_question: CityQuestion) -> CityQuestion:
        """질문을 업데이트합니다.

        Args:
            city_question: 업데이트할 질문 엔티티

        Returns:
            업데이트된 질문 엔티티
        """
