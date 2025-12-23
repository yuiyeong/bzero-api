"""도시 질문 API 엔드포인트."""

from typing import Annotated

from fastapi import APIRouter, Query

from bzero.application.use_cases.city_questions.get_city_questions import (
    GetCityQuestionsUseCase,
)
from bzero.presentation.api.dependencies import (
    CurrentCityQuestionService,
)
from bzero.presentation.schemas.city_question import (
    CityQuestionResponse,
)
from bzero.presentation.schemas.common import ListResponse, Pagination


router = APIRouter(prefix="/city-questions", tags=["city-questions"])


@router.get(
    "",
    response_model=ListResponse[CityQuestionResponse],
    summary="도시별 질문 목록 조회",
    description="특정 도시의 활성화된 질문 목록을 조회합니다. display_order 순으로 정렬됩니다.",
)
async def get_city_questions(
    city_question_service: CurrentCityQuestionService,
    city_id: Annotated[str, Query(description="도시 ID (UUID v7 hex)")],
) -> ListResponse[CityQuestionResponse]:
    """도시별 질문 목록을 조회합니다.

    Args:
        city_question_service: 도시 질문 도메인 서비스
        city_id: 도시 ID

    Returns:
        ListResponse[CityQuestionResponse]: 질문 목록
    """
    use_case = GetCityQuestionsUseCase(
        city_question_service=city_question_service,
    )
    result = await use_case.execute(city_id=city_id)
    return ListResponse(
        list=[CityQuestionResponse.create_from(item) for item in result.items],
        pagination=Pagination(total=result.total, offset=result.offset, limit=result.limit),
    )
