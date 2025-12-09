from abc import ABC, abstractmethod

from bzero.domain.entities.questionnaire import Questionnaire
from bzero.domain.value_objects import Id


class QuestionnaireRepository(ABC):
    """문답지 리포지토리 인터페이스"""

    @abstractmethod
    async def find_by_id(self, questionnaire_id: Id) -> Questionnaire | None:
        """ID로 문답지 조회"""
        pass

    @abstractmethod
    async def find_by_user_and_city(self, user_id: Id, city_id: Id) -> Questionnaire | None:
        """사용자 ID와 도시 ID로 문답지 조회 (중복 작성 방지)"""
        pass

    @abstractmethod
    async def find_by_user_id(self, user_id: Id, offset: int = 0, limit: int = 20) -> list[Questionnaire]:
        """사용자 ID로 문답지 목록 조회 (created_at 역순 정렬)"""
        pass

    @abstractmethod
    async def count_by_user_id(self, user_id: Id) -> int:
        """사용자 ID로 문답지 개수 조회"""
        pass

    @abstractmethod
    async def save(self, questionnaire: Questionnaire) -> Questionnaire:
        """문답지 저장 (생성 또는 업데이트)"""
        pass
