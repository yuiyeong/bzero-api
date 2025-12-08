from datetime import date, datetime

from pydantic import BaseModel, Field

from bzero.application.results.diary_result import DiaryResult


class CreateDiaryRequest(BaseModel):
    """일기 작성 요청 스키마"""

    title: str | None = Field(None, max_length=100, description="일기 제목 (선택)")
    content: str = Field(..., max_length=500, description="일기 내용 (최대 500자)")
    mood: str = Field(..., description="기분 이모지 (😊😐😢😠🥰 중 하나)")
    diary_date: date = Field(..., description="일기 날짜 (ISO 8601: YYYY-MM-DD)")
    city_id: str | None = Field(None, description="도시 ID (선택)")


class DiaryResponse(BaseModel):
    """일기 응답 스키마"""

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
    def from_result(cls, result: DiaryResult) -> "DiaryResponse":
        """DiaryResult로부터 DiaryResponse를 생성합니다."""
        return cls(
            diary_id=result.diary_id,
            user_id=result.user_id,
            title=result.title,
            content=result.content,
            mood=result.mood,
            diary_date=result.diary_date,
            city_id=result.city_id,
            has_earned_points=result.has_earned_points,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )


class DiaryListResponse(BaseModel):
    """일기 목록 응답 스키마"""

    diaries: list[DiaryResponse]
    total: int
    offset: int
    limit: int
