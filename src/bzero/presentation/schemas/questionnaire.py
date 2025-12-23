from datetime import datetime

from pydantic import BaseModel, Field

from bzero.application.results.questionnaire_result import QuestionnaireResult


class CreateQuestionnaireRequest(BaseModel):
    """문답지 생성 요청 스키마."""

    city_question_id: str = Field(
        ...,
        description="질문 ID (UUID v7 hex)",
    )
    answer: str = Field(
        ...,
        min_length=1,
        description="답변 내용",
    )


class UpdateQuestionnaireRequest(BaseModel):
    """문답지 수정 요청 스키마."""

    answer: str = Field(
        ...,
        min_length=1,
        description="답변 내용",
    )


class QuestionnaireResponse(BaseModel):
    """문답지 응답 스키마."""

    questionnaire_id: str = Field(..., description="문답지 ID (UUID v7 hex)")
    user_id: str = Field(..., description="작성자 ID (UUID v7 hex)")
    room_stay_id: str = Field(..., description="체류 ID (UUID v7 hex)")
    city_question_id: str = Field(..., description="질문 ID (UUID v7 hex)")
    city_question: str = Field(..., description="도시 질문 내용 (스냅샷)")
    answer: str = Field(..., description="답변 내용")
    city_id: str = Field(..., description="도시 ID (UUID v7 hex)")
    guest_house_id: str = Field(..., description="게스트하우스 ID (UUID v7 hex)")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    @classmethod
    def create_from(cls, result: QuestionnaireResult) -> "QuestionnaireResponse":
        """QuestionnaireResult로부터 QuestionnaireResponse를 생성합니다.

        Args:
            result: 문답지 유스케이스 결과 객체

        Returns:
            QuestionnaireResponse: 문답지 응답 스키마
        """
        return cls(
            questionnaire_id=result.questionnaire_id,
            user_id=result.user_id,
            room_stay_id=result.room_stay_id,
            city_question_id=result.city_question_id,
            city_question=result.city_question,
            answer=result.answer,
            city_id=result.city_id,
            guest_house_id=result.guest_house_id,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
