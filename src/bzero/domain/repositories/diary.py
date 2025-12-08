from abc import ABC, abstractmethod
from datetime import date

from bzero.domain.entities.diary import Diary
from bzero.domain.value_objects import Id


class DiaryRepository(ABC):
    """일기 리포지토리 인터페이스"""

    @abstractmethod
    async def find_by_id(self, diary_id: Id) -> Diary | None:
        """ID로 일기 조회"""
        pass

    @abstractmethod
    async def find_by_user_and_date(self, user_id: Id, diary_date: date) -> Diary | None:
        """사용자 ID와 날짜로 일기 조회 (중복 작성 방지)"""
        pass

    @abstractmethod
    async def find_by_user_id(self, user_id: Id, offset: int = 0, limit: int = 20) -> list[Diary]:
        """사용자 ID로 일기 목록 조회 (diary_date 역순 정렬)"""
        pass

    @abstractmethod
    async def count_by_user_id(self, user_id: Id) -> int:
        """사용자 ID로 일기 개수 조회"""
        pass

    @abstractmethod
    async def save(self, diary: Diary) -> Diary:
        """일기 저장 (생성 또는 업데이트)"""
        pass
