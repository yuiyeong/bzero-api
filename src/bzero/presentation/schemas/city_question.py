from datetime import datetime

from pydantic import BaseModel, Field

from bzero.application.results.city_question_result import CityQuestionResult


class CityQuestionResponse(BaseModel):
    """도시 질문 응답 스키마."""

    city_question_id: str = Field(..., description="질문 ID (UUID v7 hex)")
    city_id: str = Field(..., description="도시 ID (UUID v7 hex)")
    question: str = Field(..., description="질문 내용")
    display_order: int = Field(..., description="표시 순서")
    is_active: bool = Field(..., description="활성화 여부")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    @classmethod
    def create_from(cls, result: CityQuestionResult) -> "CityQuestionResponse":
        """CityQuestionResult로부터 CityQuestionResponse를 생성합니다.

        Args:
            result: 도시 질문 유스케이스 결과 객체

        Returns:
            CityQuestionResponse: 도시 질문 응답 스키마
        """
        return cls(
            city_question_id=result.city_question_id,
            city_id=result.city_id,
            question=result.question,
            display_order=result.display_order,
            is_active=result.is_active,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
