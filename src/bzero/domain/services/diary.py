from datetime import datetime
from zoneinfo import ZoneInfo

from bzero.domain.entities.diary import Diary
from bzero.domain.errors import DuplicatedDiaryError, NotFoundDiaryError
from bzero.domain.repositories.diary import DiaryRepository
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.diary import DiaryMood


class DiaryService:
    """일기 도메인 서비스.

    일기 CRUD 및 비즈니스 로직을 처리합니다.
    포인트 지급은 유스케이스에서 PointTransactionService를 통해 처리합니다.
    """

    def __init__(
        self,
        diary_repository: DiaryRepository,
        timezone: ZoneInfo,
    ) -> None:
        """DiaryService를 초기화합니다.

        Args:
            diary_repository: 일기 리포지토리
            timezone: 시간대 정보
        """
        self._diary_repository = diary_repository
        self._timezone = timezone

    async def create_diary(
        self,
        user_id: Id,
        room_stay_id: Id,
        city_id: Id,
        guest_house_id: Id,
        title: str,
        content: str,
        mood: DiaryMood,
    ) -> Diary:
        """새 일기를 생성합니다.

        Args:
            user_id: 작성자 ID
            room_stay_id: 체류 ID
            city_id: 도시 ID
            guest_house_id: 게스트하우스 ID
            title: 일기 제목
            content: 일기 내용
            mood: 감정 상태

        Returns:
            생성된 일기 엔티티

        Raises:
            DuplicatedDiaryError: 해당 체류에 이미 일기가 존재할 경우
        """
        if await self._diary_repository.exists_by_room_stay_id(room_stay_id):
            raise DuplicatedDiaryError

        now = datetime.now(self._timezone)
        diary = Diary.create(
            user_id=user_id,
            room_stay_id=room_stay_id,
            city_id=city_id,
            guest_house_id=guest_house_id,
            title=title,
            content=content,
            mood=mood,
            created_at=now,
            updated_at=now,
        )

        return await self._diary_repository.create(diary)

    async def get_diary_by_id(self, diary_id: Id) -> Diary:
        """일기 ID로 조회합니다.

        Args:
            diary_id: 일기 ID

        Returns:
            일기 엔티티

        Raises:
            NotFoundDiaryError: 일기가 존재하지 않을 경우
        """
        diary = await self._diary_repository.find_by_diary_id(diary_id)
        if diary is None:
            raise NotFoundDiaryError
        return diary

    async def get_diary_by_room_stay_id(self, room_stay_id: Id) -> Diary | None:
        """체류 ID로 일기를 조회합니다.

        Args:
            room_stay_id: 체류 ID

        Returns:
            일기 엔티티 또는 None
        """
        return await self._diary_repository.find_by_room_stay_id(room_stay_id)

    async def get_diaries_by_user_id(
        self,
        user_id: Id,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Diary], int]:
        """사용자의 일기 목록을 페이지네이션으로 조회합니다.

        Args:
            user_id: 사용자 ID
            limit: 조회 개수
            offset: 오프셋

        Returns:
            (일기 목록, 전체 개수) 튜플
        """
        diaries = await self._diary_repository.find_all_by_user_id(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
        total = await self._diary_repository.count_by_user_id(user_id)
        return diaries, total

    async def update_diary(
        self,
        diary_id: Id,
        title: str,
        content: str,
        mood: DiaryMood,
    ) -> Diary:
        """일기를 수정합니다.

        Args:
            diary_id: 일기 ID
            title: 새 일기 제목
            content: 새 일기 내용
            mood: 새 감정 상태

        Returns:
            수정된 일기 엔티티

        Raises:
            NotFoundDiaryError: 일기가 존재하지 않을 경우
        """
        diary = await self.get_diary_by_id(diary_id)
        now = datetime.now(self._timezone)
        diary.update_content(
            title=title,
            content=content,
            mood=mood,
            updated_at=now,
        )
        return await self._diary_repository.update(diary)

    async def delete_diary(self, diary_id: Id) -> Diary:
        """일기를 삭제합니다 (soft delete).

        Args:
            diary_id: 일기 ID

        Returns:
            삭제된 일기 엔티티

        Raises:
            NotFoundDiaryError: 일기가 존재하지 않을 경우
        """
        diary = await self.get_diary_by_id(diary_id)
        now = datetime.now(self._timezone)
        diary.soft_delete(deleted_at=now)
        return await self._diary_repository.update(diary)
