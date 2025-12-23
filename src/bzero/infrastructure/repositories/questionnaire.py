"""SQLAlchemy 기반 Questionnaire Repository.

비동기 리포지토리 구현체입니다.
QuestionnaireRepositoryCore의 동기 메서드를 run_sync로 호출합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.questionnaire import Questionnaire
from bzero.domain.repositories.questionnaire import QuestionnaireRepository
from bzero.domain.value_objects import Id
from bzero.infrastructure.repositories.questionnaire_core import QuestionnaireRepositoryCore


class SqlAlchemyQuestionnaireRepository(QuestionnaireRepository):
    """SQLAlchemy 기반 Questionnaire Repository (비동기).

    QuestionnaireRepositoryCore의 동기 메서드를 run_sync로 호출합니다.
    이 패턴을 통해 로직 중복 없이 비동기 인터페이스를 제공합니다.
    """

    def __init__(self, session: AsyncSession):
        """리포지토리를 초기화합니다.

        Args:
            session: SQLAlchemy AsyncSession 인스턴스
        """
        self._session = session

    async def create(self, questionnaire: Questionnaire) -> Questionnaire:
        """문답지를 생성합니다.

        Args:
            questionnaire: 생성할 문답지 엔티티

        Returns:
            생성된 문답지
        """
        return await self._session.run_sync(QuestionnaireRepositoryCore.create, questionnaire)

    async def find_by_id(self, questionnaire_id: Id) -> Questionnaire | None:
        """ID로 문답지를 조회합니다.

        Args:
            questionnaire_id: 문답지 ID

        Returns:
            문답지 또는 None
        """
        return await self._session.run_sync(QuestionnaireRepositoryCore.find_by_id, questionnaire_id)

    async def find_by_room_stay_and_question(
        self,
        room_stay_id: Id,
        city_question_id: Id,
    ) -> Questionnaire | None:
        """체류 ID와 질문 ID로 문답지를 조회합니다.

        Args:
            room_stay_id: 체류 ID
            city_question_id: 질문 ID

        Returns:
            문답지 또는 None
        """
        return await self._session.run_sync(
            QuestionnaireRepositoryCore.find_by_room_stay_and_question,
            room_stay_id,
            city_question_id,
        )

    async def find_all_by_user_id(
        self,
        user_id: Id,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Questionnaire]:
        """사용자의 모든 문답지를 조회합니다.

        Args:
            user_id: 사용자 ID
            limit: 조회할 최대 개수
            offset: 건너뛸 개수

        Returns:
            문답지 목록
        """
        return await self._session.run_sync(
            QuestionnaireRepositoryCore.find_all_by_user_id,
            user_id,
            limit,
            offset,
        )

    async def find_all_by_room_stay_id(self, room_stay_id: Id) -> list[Questionnaire]:
        """체류 ID로 모든 문답지를 조회합니다.

        Args:
            room_stay_id: 체류 ID

        Returns:
            문답지 목록
        """
        return await self._session.run_sync(QuestionnaireRepositoryCore.find_all_by_room_stay_id, room_stay_id)

    async def count_by_user_id(self, user_id: Id) -> int:
        """사용자의 문답지 총 개수를 조회합니다.

        Args:
            user_id: 사용자 ID

        Returns:
            문답지 총 개수
        """
        return await self._session.run_sync(QuestionnaireRepositoryCore.count_by_user_id, user_id)

    async def update(self, questionnaire: Questionnaire) -> Questionnaire:
        """문답지를 업데이트합니다.

        Args:
            questionnaire: 업데이트할 문답지 엔티티

        Returns:
            업데이트된 문답지

        Raises:
            NotFoundQuestionnaireError: 문답지를 찾을 수 없는 경우
        """
        return await self._session.run_sync(QuestionnaireRepositoryCore.update, questionnaire)

    async def exists_by_room_stay_and_question(
        self,
        room_stay_id: Id,
        city_question_id: Id,
    ) -> bool:
        """체류 ID와 질문 ID로 존재 여부를 확인합니다.

        Args:
            room_stay_id: 체류 ID
            city_question_id: 질문 ID

        Returns:
            존재 여부
        """
        return await self._session.run_sync(
            QuestionnaireRepositoryCore.exists_by_room_stay_and_question,
            room_stay_id,
            city_question_id,
        )
