"""SQLAlchemy 기반 Diary Repository.

비동기 리포지토리 구현체입니다.
DiaryRepositoryCore의 동기 메서드를 run_sync로 호출합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.diary import Diary
from bzero.domain.repositories.diary import DiaryRepository
from bzero.domain.value_objects import Id
from bzero.infrastructure.repositories.diary_core import DiaryRepositoryCore


class SqlAlchemyDiaryRepository(DiaryRepository):
    """SQLAlchemy 기반 Diary Repository (비동기).

    DiaryRepositoryCore의 동기 메서드를 run_sync로 호출합니다.
    이 패턴을 통해 로직 중복 없이 비동기 인터페이스를 제공합니다.

    Attributes:
        _session: SQLAlchemy AsyncSession 인스턴스
    """

    def __init__(self, session: AsyncSession):
        """리포지토리를 초기화합니다.

        Args:
            session: SQLAlchemy AsyncSession 인스턴스
        """
        self._session = session

    async def create(self, diary: Diary) -> Diary:
        """일기를 생성합니다.

        Args:
            diary: 생성할 일기 엔티티

        Returns:
            생성된 일기 (DB에서 생성된 타임스탬프 포함)
        """
        return await self._session.run_sync(DiaryRepositoryCore.create, diary)

    async def find_by_diary_id(self, diary_id: Id) -> Diary | None:
        """ID로 일기를 조회합니다.

        Args:
            diary_id: 조회할 일기 ID

        Returns:
            조회된 일기 또는 None
        """
        return await self._session.run_sync(DiaryRepositoryCore.find_by_diary_id, diary_id)

    async def find_by_room_stay_id(self, room_stay_id: Id) -> Diary | None:
        """체류 ID로 일기를 조회합니다.

        Args:
            room_stay_id: 체류 ID

        Returns:
            조회된 일기 또는 None
        """
        return await self._session.run_sync(DiaryRepositoryCore.find_by_room_stay_id, room_stay_id)

    async def find_all_by_user_id(
        self,
        user_id: Id,
        limit: int,
        offset: int,
    ) -> list[Diary]:
        """사용자의 모든 일기를 조회합니다.

        Args:
            user_id: 사용자 ID
            limit: 조회할 최대 개수
            offset: 건너뛸 개수

        Returns:
            일기 목록
        """
        return await self._session.run_sync(
            DiaryRepositoryCore.find_all_by_user_id,
            user_id,
            limit,
            offset,
        )

    async def count_by_user_id(self, user_id: Id) -> int:
        """사용자의 일기 총 개수를 조회합니다.

        Args:
            user_id: 사용자 ID

        Returns:
            일기 총 개수
        """
        return await self._session.run_sync(DiaryRepositoryCore.count_by_user_id, user_id)

    async def update(self, diary: Diary) -> Diary:
        """일기를 업데이트합니다.

        Args:
            diary: 업데이트할 일기 엔티티

        Returns:
            업데이트된 일기

        Raises:
            NotFoundDiaryError: 일기를 찾을 수 없는 경우
        """
        return await self._session.run_sync(DiaryRepositoryCore.update, diary)

    async def exists_by_room_stay_id(self, room_stay_id: Id) -> bool:
        """체류 ID로 일기 존재 여부를 확인합니다.

        Args:
            room_stay_id: 체류 ID

        Returns:
            일기 존재 여부
        """
        return await self._session.run_sync(DiaryRepositoryCore.exists_by_room_stay_id, room_stay_id)
