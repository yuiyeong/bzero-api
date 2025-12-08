from datetime import date

from bzero.domain.entities.diary import Diary
from bzero.domain.errors import DiaryNotFoundError
from bzero.domain.repositories.diary import DiaryRepository
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.diary import DiaryContent, DiaryMood


class DiaryService:
    """일기 도메인 서비스

    Diary 생성 및 조회를 담당합니다.
    주의: 모든 메서드는 데이터베이스 트랜잭션 내에서 호출되어야 합니다.
    """

    def __init__(self, diary_repository: DiaryRepository):
        self._diary_repository = diary_repository

    async def create_diary(
        self,
        user_id: Id,
        title: str | None,
        content: DiaryContent,
        mood: DiaryMood,
        diary_date: date,
        city_id: Id | None,
    ) -> Diary:
        """일기를 생성합니다.

        Args:
            user_id: 사용자 ID
            title: 일기 제목 (optional)
            content: 일기 내용
            mood: 기분 이모지
            diary_date: 일기 날짜
            city_id: 도시 ID (optional)

        Returns:
            생성된 Diary 엔티티
        """
        from datetime import datetime
        from zoneinfo import ZoneInfo

        now = datetime.now(ZoneInfo("Asia/Seoul"))

        diary = Diary.create(
            user_id=user_id,
            title=title,
            content=content,
            mood=mood,
            diary_date=diary_date,
            city_id=city_id,
            created_at=now,
            updated_at=now,
        )

        return await self._diary_repository.save(diary)

    async def get_diary_by_id(self, diary_id: Id) -> Diary:
        """일기 ID로 일기를 조회합니다.

        Args:
            diary_id: 조회할 일기의 ID

        Returns:
            조회된 Diary 엔티티

        Raises:
            DiaryNotFoundError: 일기가 존재하지 않을 때
        """
        diary = await self._diary_repository.find_by_id(diary_id)
        if diary is None:
            raise DiaryNotFoundError

        return diary

    async def get_diary_by_user_and_date(self, user_id: Id, diary_date: date) -> Diary | None:
        """사용자와 날짜로 일기를 조회합니다. (중복 작성 방지용)

        Args:
            user_id: 사용자 ID
            diary_date: 일기 날짜

        Returns:
            조회된 Diary 엔티티 또는 None
        """
        return await self._diary_repository.find_by_user_and_date(user_id, diary_date)

    async def get_diaries_by_user(
        self,
        user_id: Id,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Diary], int]:
        """사용자의 일기 목록을 조회합니다.

        diary_date 역순(최신순)으로 정렬하여 반환합니다.

        Args:
            user_id: 사용자 ID
            offset: 조회 시작 위치 (기본값: 0)
            limit: 조회할 최대 개수 (기본값: 20)

        Returns:
            (일기 목록, 전체 개수) 튜플
        """
        return await self._diary_repository.find_by_user_id(user_id, offset, limit)
