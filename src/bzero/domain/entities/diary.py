from dataclasses import dataclass
from datetime import date, datetime

from bzero.domain.value_objects import Id
from bzero.domain.value_objects.diary import DiaryContent, DiaryMood


@dataclass
class Diary:
    """일기 엔티티

    사용자가 작성한 일기를 나타냅니다.
    하루 1회 작성 가능하며, 작성 시 50P 지급됩니다.
    """

    diary_id: Id
    user_id: Id
    title: str | None  # 일기 제목 (optional, max 100자)
    content: DiaryContent  # 일기 내용 (max 500자)
    mood: DiaryMood  # 기분 이모지 (😊😐😢😠🥰)
    diary_date: date  # 일기 날짜
    city_id: Id | None  # 도시 ID (optional)
    has_earned_points: bool  # 포인트 획득 여부

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    def mark_points_earned(self) -> None:
        """포인트 획득 처리"""
        self.has_earned_points = True

    @classmethod
    def create(
        cls,
        user_id: Id,
        title: str | None,
        content: DiaryContent,
        mood: DiaryMood,
        diary_date: date,
        city_id: Id | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Diary":
        """Diary 엔티티를 생성합니다."""
        return cls(
            diary_id=Id(),
            user_id=user_id,
            title=title,
            content=content,
            mood=mood,
            diary_date=diary_date,
            city_id=city_id,
            has_earned_points=False,
            created_at=created_at,
            updated_at=updated_at,
        )
