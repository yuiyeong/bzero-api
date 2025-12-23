from abc import ABC, abstractmethod

from bzero.domain.entities.diary import Diary
from bzero.domain.value_objects import Id


class DiaryRepository(ABC):
    """일기 리포지토리 인터페이스 (비동기)."""

    @abstractmethod
    async def create(self, diary: Diary) -> Diary:
        """일기를 생성합니다.

        Args:
            diary: 생성할 일기 엔티티

        Returns:
            생성된 일기 엔티티
        """

    @abstractmethod
    async def find_by_diary_id(self, diary_id: Id) -> Diary | None:
        """일기 ID로 조회합니다.

        Args:
            diary_id: 일기 ID

        Returns:
            일기 엔티티 또는 None
        """

    @abstractmethod
    async def find_by_room_stay_id(self, room_stay_id: Id) -> Diary | None:
        """체류 ID로 일기를 조회합니다.

        체류당 1개의 일기만 존재하므로 단일 결과 반환.

        Args:
            room_stay_id: 체류 ID

        Returns:
            일기 엔티티 또는 None
        """

    @abstractmethod
    async def find_all_by_user_id(
        self,
        user_id: Id,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Diary]:
        """사용자의 모든 일기를 페이지네이션으로 조회합니다.

        Args:
            user_id: 사용자 ID
            limit: 조회 개수 (기본 20)
            offset: 오프셋 (기본 0)

        Returns:
            일기 목록 (최신순)
        """

    @abstractmethod
    async def count_by_user_id(self, user_id: Id) -> int:
        """사용자의 일기 총 개수를 조회합니다.

        Args:
            user_id: 사용자 ID

        Returns:
            일기 총 개수
        """

    @abstractmethod
    async def update(self, diary: Diary) -> Diary:
        """일기를 업데이트합니다.

        Args:
            diary: 업데이트할 일기 엔티티

        Returns:
            업데이트된 일기 엔티티
        """

    @abstractmethod
    async def exists_by_room_stay_id(self, room_stay_id: Id) -> bool:
        """해당 체류에 일기가 존재하는지 확인합니다.

        중복 작성 방지를 위한 메서드.

        Args:
            room_stay_id: 체류 ID

        Returns:
            존재 여부
        """
