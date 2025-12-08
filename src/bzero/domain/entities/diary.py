from dataclasses import dataclass
from datetime import date, datetime

from bzero.domain.value_objects import DiaryContent, DiaryMood, Id


@dataclass
class Diary:
    """일기 엔티티

    사용자의 하루 일기를 나타냅니다.
    하루에 하나의 일기만 작성 가능합니다.
    """

    diary_id: Id
    user_id: Id
    title: str | None  # 제목 (nullable, 최대 100자)
    content: DiaryContent  # 내용 (최대 500자)
    mood: DiaryMood  # 기분 이모지
    diary_date: date  # 일기 날짜
    city_id: Id | None  # 관련 도시 (nullable)
    has_earned_points: bool  # 포인트 지급 여부 (하루 1회)

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @classmethod
    def create(
        cls,
        user_id: Id,
        content: DiaryContent,
        mood: DiaryMood,
        diary_date: date,
        created_at: datetime,
        updated_at: datetime,
        title: str | None = None,
        city_id: Id | None = None,
    ) -> "Diary":
        """새 Diary 엔티티를 생성합니다 (ID 자동 생성)."""
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

    def mark_points_earned(self) -> None:
        """포인트 지급 완료 표시"""
        self.has_earned_points = True
