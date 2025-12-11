"""문답지 관련 API 엔드포인트."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from bzero.application.use_cases.questionnaires.create_questionnaire import CreateQuestionnaireUseCase
from bzero.application.use_cases.questionnaires.get_questionnaire_by_id import GetQuestionnaireByIdUseCase
from bzero.application.use_cases.questionnaires.get_questionnaires import GetQuestionnairesUseCase
from bzero.presentation.api.dependencies import (
    CurrentJWTPayload,
    CurrentPointTransactionService,
    CurrentQuestionnaireService,
    CurrentUserService,
    DBSession,
)
from bzero.presentation.schemas.common import DataResponse
from bzero.presentation.schemas.questionnaire import (
    CreateQuestionnaireRequest,
    QuestionnaireListResponse,
    QuestionnaireResponse,
)


router = APIRouter(prefix="/questionnaires", tags=["questionnaires"])


@router.post(
    "",
    response_model=DataResponse[QuestionnaireResponse],
    status_code=status.HTTP_201_CREATED,
    summary="문답지 작성",
    description="도시별 문답지를 작성하고 포인트를 지급합니다 (50P, 도시별 1회).",
)
async def create_questionnaire(
    request: CreateQuestionnaireRequest,
    session: DBSession,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    questionnaire_service: CurrentQuestionnaireService,
    point_transaction_service: CurrentPointTransactionService,
) -> DataResponse[QuestionnaireResponse]:
    """문답지 작성.

    - 도시별로 하나의 문답지만 작성 가능 (중복 시 409 Conflict)
    - 작성 시 50P 자동 지급 (도시별 1회)
    """
    result = await CreateQuestionnaireUseCase(
        session=session,
        user_service=user_service,
        questionnaire_service=questionnaire_service,
        point_transaction_service=point_transaction_service,
    ).execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        city_id=request.city_id,
        question_1_answer=request.question_1_answer,
        question_2_answer=request.question_2_answer,
        question_3_answer=request.question_3_answer,
    )

    return DataResponse(data=QuestionnaireResponse.create_from(result))


@router.get(
    "",
    response_model=QuestionnaireListResponse,
    summary="문답지 목록 조회",
    description="사용자의 문답지 목록을 최신순으로 조회합니다.",
)
async def get_questionnaires(
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    questionnaire_service: CurrentQuestionnaireService,
    offset: Annotated[int, Query(ge=0, description="조회 시작 위치")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="조회할 최대 개수")] = 20,
) -> QuestionnaireListResponse:
    """문답지 목록 조회.

    - 본인이 작성한 문답지만 조회 가능
    - created_at 역순 정렬 (최신순)
    - pagination 지원 (기본값: offset=0, limit=20)
    """
    result = await GetQuestionnairesUseCase(user_service, questionnaire_service).execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        offset=offset,
        limit=limit,
    )

    return QuestionnaireListResponse(
        questionnaires=[QuestionnaireResponse.create_from(item) for item in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.get(
    "/{questionnaire_id}",
    response_model=DataResponse[QuestionnaireResponse],
    summary="문답지 상세 조회",
    description="문답지 ID로 특정 문답지를 조회합니다.",
)
async def get_questionnaire_by_id(
    questionnaire_id: str,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    questionnaire_service: CurrentQuestionnaireService,
) -> DataResponse[QuestionnaireResponse]:
    """문답지 상세 조회.

    - 본인이 작성한 문답지만 조회 가능 (다른 사용자 문답지 조회 시 404)
    - 존재하지 않는 문답지 조회 시 404
    """
    result = await GetQuestionnaireByIdUseCase(user_service, questionnaire_service).execute(
        questionnaire_id=questionnaire_id,
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
    )

    return DataResponse(data=QuestionnaireResponse.create_from(result))
