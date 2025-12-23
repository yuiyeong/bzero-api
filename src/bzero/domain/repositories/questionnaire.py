from abc import ABC, abstractmethod

from bzero.domain.entities.questionnaire import Questionnaire
from bzero.domain.value_objects import Id


class QuestionnaireRepository(ABC):
    """문답지 리포지토리 인터페이스 (비동기)."""

    @abstractmethod
    async def create(self, questionnaire: Questionnaire) -> Questionnaire:
        """문답지를 생성합니다.

        Args:
            questionnaire: 생성할 문답지 엔티티

        Returns:
            생성된 문답지 엔티티
        """

    @abstractmethod
    async def find_by_id(self, questionnaire_id: Id) -> Questionnaire | None:
        """문답지 ID로 조회합니다.

        Args:
            questionnaire_id: 문답지 ID

        Returns:
            문답지 엔티티 또는 None
        """

    @abstractmethod
    async def find_by_room_stay_and_question(
        self,
        room_stay_id: Id,
        city_question_id: Id,
    ) -> Questionnaire | None:
        """체류 ID와 질문 ID로 문답지를 조회합니다.

        중복 방지 검증 및 기존 답변 조회용.

        Args:
            room_stay_id: 체류 ID
            city_question_id: 질문 ID

        Returns:
            문답지 엔티티 또는 None
        """

    @abstractmethod
    async def find_all_by_user_id(
        self,
        user_id: Id,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Questionnaire]:
        """사용자의 모든 문답지를 페이지네이션으로 조회합니다.

        Args:
            user_id: 사용자 ID
            limit: 조회 개수 (기본 20)
            offset: 오프셋 (기본 0)

        Returns:
            문답지 목록 (최신순)
        """

    @abstractmethod
    async def find_all_by_room_stay_id(self, room_stay_id: Id) -> list[Questionnaire]:
        """체류 ID로 모든 문답지를 조회합니다.

        Args:
            room_stay_id: 체류 ID

        Returns:
            문답지 목록
        """

    @abstractmethod
    async def count_by_user_id(self, user_id: Id) -> int:
        """사용자의 문답지 총 개수를 조회합니다.

        Args:
            user_id: 사용자 ID

        Returns:
            문답지 총 개수
        """

    @abstractmethod
    async def update(self, questionnaire: Questionnaire) -> Questionnaire:
        """문답지를 업데이트합니다.

        Args:
            questionnaire: 업데이트할 문답지 엔티티

        Returns:
            업데이트된 문답지 엔티티
        """

    @abstractmethod
    async def exists_by_room_stay_and_question(
        self,
        room_stay_id: Id,
        city_question_id: Id,
    ) -> bool:
        """해당 체류에서 해당 질문에 대한 답변이 존재하는지 확인합니다.

        중복 작성 방지를 위한 메서드.

        Args:
            room_stay_id: 체류 ID
            city_question_id: 질문 ID

        Returns:
            존재 여부
        """
