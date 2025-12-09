from datetime import date, datetime

from pydantic import BaseModel, Field

from bzero.application.results.diary_result import DiaryResult


class CreateDiaryRequest(BaseModel):
    """일기 작성 요청 스키마"""

    title: str | None = Field(None, max_length=100, description="제목 (선택, 최대 100자)")
    content: str = Field(..., min_length=1, max_length=500, description="내용 (최대 500자)")
    mood: str = Field(..., description="기분 이모지 (😊😐😢😠🥰 중 하나)")
    city_id: str | None = Field(None, description="관련 도시 ID (선택)")


class DiaryResponse(BaseModel):
    """일기 응답 스키마"""

    diary_id: str = Field(..., description="일기 ID (UUID v7)")
    user_id: str = Field(..., description="사용자 ID")
    title: str | None = Field(None, description="제목")
    content: str = Field(..., description="내용")
    mood: str = Field(..., description="기분 이모지")
    diary_date: date = Field(..., description="일기 날짜")
    city_id: str | None = Field(None, description="관련 도시 ID")
    has_earned_points: bool = Field(..., description="포인트 지급 여부")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    model_config = {"from_attributes": True}

    @classmethod
    def create_from(cls, result: DiaryResult) -> "DiaryResponse":
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

    diaries: list[DiaryResponse] = Field(..., description="일기 목록")
    total: int = Field(..., description="전체 개수")
    offset: int = Field(..., description="오프셋")
    limit: int = Field(..., description="제한")
