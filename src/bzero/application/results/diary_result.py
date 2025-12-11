from dataclasses import dataclass
from datetime import date, datetime

from bzero.domain.entities.diary import Diary


@dataclass(frozen=True)
class DiaryResult:
    """UseCase에서 반환하는 Diary 결과 객체"""

    diary_id: str
    user_id: str
    title: str | None
    content: str
    mood: str
    diary_date: date
    city_id: str | None
    has_earned_points: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_from(cls, entity: Diary) -> "DiaryResult":
        return cls(
            diary_id=entity.diary_id.value.hex,
            user_id=entity.user_id.value.hex,
            title=entity.title,
            content=entity.content.value,
            mood=entity.mood.value,
            diary_date=entity.diary_date,
            city_id=entity.city_id.value.hex if entity.city_id else None,
            has_earned_points=entity.has_earned_points,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
