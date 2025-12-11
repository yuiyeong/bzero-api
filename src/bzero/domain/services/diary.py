from datetime import date, datetime
from zoneinfo import ZoneInfo

from bzero.domain.entities.diary import Diary
from bzero.domain.entities.ticket import Ticket
from bzero.domain.errors import DuplicatedDiaryError, NotFoundDiaryError
from bzero.domain.repositories.diary import DiaryRepository
from bzero.domain.value_objects import DiaryContent, DiaryMood, Id


class DiaryService:
    """일기 도메인 서비스

    Diary 생성/조회를 담당합니다.
    주의: 모든 메서드는 데이터베이스 트랜잭션 내에서 호출되어야 합니다.
    """

    def __init__(self, diary_repository: DiaryRepository, timezone: ZoneInfo):
        self._diary_repository = diary_repository
        self._timezone = timezone

    def calculate_diary_date(self, latest_completed_ticket: Ticket | None) -> date:
        """일기 날짜를 계산합니다.

        TODO: 추후 room_stays 테이블 구현 시 교체 필요
        - room_stays의 check_in_time을 기준으로 일기 날짜 계산
        - 현재는 임시로 단순히 현재 날짜를 반환

        Args:
            latest_completed_ticket: 가장 최근 COMPLETED 상태의 티켓 (없으면 None)
                                     - 현재는 사용하지 않음 (room_stays 구현 전까지 임시)

        Returns:
            일기 날짜 (date) - 현재는 항상 오늘 날짜 반환
        """
        now = datetime.now(self._timezone)
        return now.date()

    async def create_diary(
        self,
        user_id: Id,
        content: DiaryContent,
        mood: DiaryMood,
        diary_date: date,
        title: str | None = None,
        city_id: Id | None = None,
    ) -> Diary:
        """일기를 생성합니다.

        Args:
            user_id: 사용자 ID
            content: 일기 내용
            mood: 기분 이모지
            diary_date: 일기 날짜
            title: 제목 (선택)
            city_id: 관련 도시 ID (선택)

        Returns:
            생성된 Diary 엔티티

        Raises:
            DuplicatedDiaryError: 같은 날짜에 이미 일기가 존재할 때
        """
        # 중복 확인
        existing_diary = await self._diary_repository.find_by_user_and_date(user_id, diary_date)
        if existing_diary:
            raise DuplicatedDiaryError

        # 일기 생성
        now = datetime.now(self._timezone)
        diary = Diary.create(
            user_id=user_id,
            content=content,
            mood=mood,
            diary_date=diary_date,
            created_at=now,
            updated_at=now,
            title=title,
            city_id=city_id,
        )

        # 저장
        return await self._diary_repository.save(diary)

    async def get_diary_by_id(self, diary_id: Id) -> Diary:
        """일기를 ID로 조회합니다.

        Args:
            diary_id: 일기 ID

        Returns:
            Diary 엔티티

        Raises:
            NotFoundDiaryError: 일기를 찾을 수 없을 때
        """
        diary = await self._diary_repository.find_by_id(diary_id)
        if not diary:
            raise NotFoundDiaryError
        return diary

    async def get_diary_by_user_and_date(self, user_id: Id, diary_date: date) -> Diary | None:
        """사용자 ID와 날짜로 일기를 조회합니다.

        Args:
            user_id: 사용자 ID
            diary_date: 일기 날짜

        Returns:
            Diary 엔티티 또는 None
        """
        return await self._diary_repository.find_by_user_and_date(user_id, diary_date)

    async def get_diaries_by_user(self, user_id: Id, offset: int = 0, limit: int = 20) -> tuple[list[Diary], int]:
        """사용자의 일기 목록을 조회합니다.

        Args:
            user_id: 사용자 ID
            offset: offset
            limit: limit

        Returns:
            (일기 목록, 전체 개수) 튜플
        """
        diaries = await self._diary_repository.find_by_user_id(user_id, offset, limit)
        total = await self._diary_repository.count_by_user_id(user_id)
        return diaries, total

    async def mark_points_earned(self, diary: Diary) -> Diary:
        """일기에 포인트 지급 완료 표시를 합니다.

        Args:
            diary: Diary 엔티티

        Returns:
            업데이트된 Diary 엔티티
        """
        diary.mark_points_earned()
        diary.updated_at = datetime.now(self._timezone)
        return await self._diary_repository.save(diary)
