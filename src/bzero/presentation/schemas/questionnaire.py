from datetime import datetime

from pydantic import BaseModel, Field

from bzero.application.results.questionnaire_result import QuestionnaireResult


class CreateQuestionnaireRequest(BaseModel):
    """문답지 작성 요청 스키마"""

    city_id: str = Field(..., description="도시 ID")
    question_1_answer: str = Field(..., min_length=1, max_length=200, description="질문 1 답변 (최대 200자)")
    question_2_answer: str = Field(..., min_length=1, max_length=200, description="질문 2 답변 (최대 200자)")
    question_3_answer: str = Field(..., min_length=1, max_length=200, description="질문 3 답변 (최대 200자)")


class QuestionnaireResponse(BaseModel):
    """문답지 응답 스키마"""

    questionnaire_id: str = Field(..., description="문답지 ID (UUID v7)")
    user_id: str = Field(..., description="사용자 ID")
    city_id: str = Field(..., description="도시 ID")
    question_1_answer: str = Field(..., description="질문 1 답변")
    question_2_answer: str = Field(..., description="질문 2 답변")
    question_3_answer: str = Field(..., description="질문 3 답변")
    has_earned_points: bool = Field(..., description="포인트 지급 여부")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    model_config = {"from_attributes": True}

    @classmethod
    def create_from(cls, result: QuestionnaireResult) -> "QuestionnaireResponse":
        return cls(
            questionnaire_id=result.questionnaire_id,
            user_id=result.user_id,
            city_id=result.city_id,
            question_1_answer=result.question_1_answer,
            question_2_answer=result.question_2_answer,
            question_3_answer=result.question_3_answer,
            has_earned_points=result.has_earned_points,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )


class QuestionnaireListResponse(BaseModel):
    """문답지 목록 응답 스키마"""

    questionnaires: list[QuestionnaireResponse] = Field(..., description="문답지 목록")
    total: int = Field(..., description="전체 개수")
    offset: int = Field(..., description="오프셋")
    limit: int = Field(..., description="제한")


class CityQuestionsResponse(BaseModel):
    """도시별 질문 응답 스키마"""

    city_id: str = Field(..., description="도시 ID")
    questions: list[str] = Field(..., description="질문 3개")
