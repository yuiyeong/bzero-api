"""Diary 관련 Result 클래스들."""

from dataclasses import dataclass
from datetime import datetime

from bzero.domain.entities.diary import Diary


@dataclass(frozen=True)
class DiaryResult:
    """일기 조회 결과.

    Attributes:
        diary_id: 일기 ID
        user_id: 작성자 ID
        room_stay_id: 체류 ID
        city_id: 도시 ID
        guest_house_id: 게스트하우스 ID
        title: 일기 제목
        content: 일기 내용
        mood: 감정 상태
        created_at: 생성 시간
        updated_at: 수정 시간
    """

    diary_id: str
    user_id: str
    room_stay_id: str
    city_id: str
    guest_house_id: str
    title: str
    content: str
    mood: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_from(cls, entity: Diary) -> "DiaryResult":
        """Diary 엔티티에서 DiaryResult를 생성합니다.

        Args:
            entity: Diary 엔티티

        Returns:
            DiaryResult 인스턴스
        """
        return cls(
            diary_id=entity.diary_id.to_hex(),
            user_id=entity.user_id.to_hex(),
            room_stay_id=entity.room_stay_id.to_hex(),
            city_id=entity.city_id.to_hex(),
            guest_house_id=entity.guest_house_id.to_hex(),
            title=entity.title,
            content=entity.content,
            mood=entity.mood.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
