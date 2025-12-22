"""일기 관련 Pydantic 스키마."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from bzero.application.results.diary_result import DiaryResult


class DiaryMoodEnum(str, Enum):
    """일기 감정 상태."""

    HAPPY = "happy"
    PEACEFUL = "peaceful"
    GRATEFUL = "grateful"
    REFLECTIVE = "reflective"
    SAD = "sad"
    ANXIOUS = "anxious"
    HOPEFUL = "hopeful"
    TIRED = "tired"


class CreateDiaryRequest(BaseModel):
    """일기 생성 요청 스키마."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="일기 제목 (1-50자)",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="일기 내용 (1-500자)",
    )
    mood: DiaryMoodEnum = Field(..., description="감정 상태")


class UpdateDiaryRequest(BaseModel):
    """일기 수정 요청 스키마."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="일기 제목 (1-50자)",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="일기 내용 (1-500자)",
    )
    mood: DiaryMoodEnum = Field(..., description="감정 상태")


class DiaryResponse(BaseModel):
    """일기 응답 스키마."""

    diary_id: str = Field(..., description="일기 ID (UUID v7 hex)")
    user_id: str = Field(..., description="작성자 ID (UUID v7 hex)")
    room_stay_id: str = Field(..., description="체류 ID (UUID v7 hex)")
    city_id: str = Field(..., description="도시 ID (UUID v7 hex)")
    guest_house_id: str = Field(..., description="게스트하우스 ID (UUID v7 hex)")
    title: str = Field(..., description="일기 제목")
    content: str = Field(..., description="일기 내용")
    mood: str = Field(..., description="감정 상태")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    @classmethod
    def create_from(cls, result: DiaryResult) -> "DiaryResponse":
        """DiaryResult로부터 DiaryResponse를 생성합니다.

        Args:
            result: 일기 유스케이스 결과 객체

        Returns:
            DiaryResponse: 일기 응답 스키마
        """
        return cls(
            diary_id=result.diary_id,
            user_id=result.user_id,
            room_stay_id=result.room_stay_id,
            city_id=result.city_id,
            guest_house_id=result.guest_house_id,
            title=result.title,
            content=result.content,
            mood=result.mood,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )


class DiaryListResponse(BaseModel):
    """일기 목록 응답 스키마."""

    items: list[DiaryResponse] = Field(..., description="일기 목록")
    total: int = Field(..., description="전체 개수")
    offset: int = Field(..., description="조회 시작 위치")
    limit: int = Field(..., description="조회한 최대 개수")
