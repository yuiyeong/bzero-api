from typing import Annotated

from fastapi import APIRouter, Query, status

from bzero.application.use_cases.questionnaires.create_questionnaire import (
    CreateQuestionnaireUseCase,
)
from bzero.application.use_cases.questionnaires.delete_questionnaire import (
    DeleteQuestionnaireUseCase,
)
from bzero.application.use_cases.questionnaires.get_questionnaire_detail import (
    GetQuestionnaireDetailUseCase,
)
from bzero.application.use_cases.questionnaires.get_questionnaires_by_user import (
    GetQuestionnairesByUserUseCase,
)
from bzero.application.use_cases.questionnaires.update_questionnaire import (
    UpdateQuestionnaireUseCase,
)
from bzero.presentation.api.dependencies import (
    CurrentCityQuestionService,
    CurrentJWTPayload,
    CurrentPointTransactionService,
    CurrentQuestionnaireService,
    CurrentRoomStayService,
    CurrentUserService,
    DBSession,
)
from bzero.presentation.schemas.common import DataResponse, ListResponse, Pagination
from bzero.presentation.schemas.questionnaire import (
    CreateQuestionnaireRequest,
    QuestionnaireResponse,
    UpdateQuestionnaireRequest,
)


router = APIRouter(prefix="/questionnaires", tags=["questionnaires"])


@router.post(
    "",
    response_model=DataResponse[QuestionnaireResponse],
    status_code=status.HTTP_201_CREATED,
    summary="문답지 작성",
    description="현재 체류 중인 게스트하우스에서 문답지를 작성합니다. 체류당 질문당 1개의 답변만 작성 가능하며, 작성 시 50P가 지급됩니다.",
)
async def create_questionnaire(
    request: CreateQuestionnaireRequest,
    jwt_payload: CurrentJWTPayload,
    session: DBSession,
    user_service: CurrentUserService,
    room_stay_service: CurrentRoomStayService,
    city_question_service: CurrentCityQuestionService,
    questionnaire_service: CurrentQuestionnaireService,
    point_transaction_service: CurrentPointTransactionService,
) -> DataResponse[QuestionnaireResponse]:
    """문답지를 작성합니다.

    Args:
        request: 문답지 생성 요청 (city_question_id, answer_text)
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        session: 데이터베이스 세션
        user_service: 사용자 도메인 서비스
        room_stay_service: 체류 도메인 서비스
        city_question_service: 도시 질문 도메인 서비스
        questionnaire_service: 문답지 도메인 서비스
        point_transaction_service: 포인트 트랜잭션 도메인 서비스

    Returns:
        QuestionnaireResponse: 생성된 문답지 정보
    """
    use_case = CreateQuestionnaireUseCase(
        session=session,
        user_service=user_service,
        room_stay_service=room_stay_service,
        city_question_service=city_question_service,
        questionnaire_service=questionnaire_service,
        point_transaction_service=point_transaction_service,
    )
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        city_question_id=request.city_question_id,
        answer_text=request.answer,
    )
    return DataResponse(data=QuestionnaireResponse.create_from(result))


@router.get(
    "",
    response_model=ListResponse[QuestionnaireResponse],
    summary="내 문답지 목록 조회",
    description="내가 작성한 문답지 목록을 조회합니다.",
)
async def get_my_questionnaires(
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    questionnaire_service: CurrentQuestionnaireService,
    offset: Annotated[int, Query(ge=0, description="조회 시작 위치")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="조회할 최대 개수")] = 20,
) -> ListResponse[QuestionnaireResponse]:
    """내 문답지 목록을 조회합니다.

    Args:
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        user_service: 사용자 도메인 서비스
        questionnaire_service: 문답지 도메인 서비스
        offset: 조회 시작 위치 (기본값: 0)
        limit: 조회할 최대 개수 (기본값: 20, 최대: 100)

    Returns:
        QuestionnaireListResponse: 문답지 목록과 페이지네이션 정보
    """
    use_case = GetQuestionnairesByUserUseCase(
        user_service=user_service,
        questionnaire_service=questionnaire_service,
    )
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        limit=limit,
        offset=offset,
    )
    return ListResponse(
        list=[QuestionnaireResponse.create_from(q) for q in result.items],
        pagination=Pagination(total=result.total, offset=result.offset, limit=result.limit),
    )


@router.get(
    "/{questionnaire_id}",
    response_model=DataResponse[QuestionnaireResponse],
    summary="문답지 상세 조회",
    description="특정 문답지의 상세 정보를 조회합니다.",
)
async def get_questionnaire_detail(
    questionnaire_id: str,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    questionnaire_service: CurrentQuestionnaireService,
) -> DataResponse[QuestionnaireResponse]:
    """문답지 상세 정보를 조회합니다.

    Args:
        questionnaire_id: 문답지 ID (UUID v7 hex)
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        user_service: 사용자 도메인 서비스
        questionnaire_service: 문답지 도메인 서비스

    Returns:
        QuestionnaireResponse: 문답지 상세 정보
    """
    use_case = GetQuestionnaireDetailUseCase(
        user_service=user_service,
        questionnaire_service=questionnaire_service,
    )
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        questionnaire_id=questionnaire_id,
    )
    return DataResponse(data=QuestionnaireResponse.create_from(result))


@router.patch(
    "/{questionnaire_id}",
    response_model=DataResponse[QuestionnaireResponse],
    summary="문답지 수정",
    description="문답지의 답변을 수정합니다.",
)
async def update_questionnaire(
    questionnaire_id: str,
    request: UpdateQuestionnaireRequest,
    jwt_payload: CurrentJWTPayload,
    session: DBSession,
    user_service: CurrentUserService,
    questionnaire_service: CurrentQuestionnaireService,
) -> DataResponse[QuestionnaireResponse]:
    """문답지를 수정합니다.

    Args:
        questionnaire_id: 문답지 ID (UUID v7 hex)
        request: 문답지 수정 요청 (answer_text)
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        session: 데이터베이스 세션
        user_service: 사용자 도메인 서비스
        questionnaire_service: 문답지 도메인 서비스

    Returns:
        QuestionnaireResponse: 수정된 문답지 정보
    """
    use_case = UpdateQuestionnaireUseCase(
        session=session,
        user_service=user_service,
        questionnaire_service=questionnaire_service,
    )
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        questionnaire_id=questionnaire_id,
        answer_text=request.answer,
    )
    return DataResponse(data=QuestionnaireResponse.create_from(result))


@router.delete(
    "/{questionnaire_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="문답지 삭제",
    description="문답지를 삭제합니다 (soft delete).",
)
async def delete_questionnaire(
    questionnaire_id: str,
    jwt_payload: CurrentJWTPayload,
    session: DBSession,
    user_service: CurrentUserService,
    questionnaire_service: CurrentQuestionnaireService,
) -> None:
    """문답지를 삭제합니다.

    Args:
        questionnaire_id: 문답지 ID (UUID v7 hex)
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        session: 데이터베이스 세션
        user_service: 사용자 도메인 서비스
        questionnaire_service: 문답지 도메인 서비스
    """
    use_case = DeleteQuestionnaireUseCase(
        session=session,
        user_service=user_service,
        questionnaire_service=questionnaire_service,
    )
    await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        questionnaire_id=questionnaire_id,
    )
