"""일기 관련 API 엔드포인트."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from bzero.application.use_cases.diaries.create_diary import CreateDiaryUseCase
from bzero.application.use_cases.diaries.get_diaries import GetDiariesUseCase
from bzero.application.use_cases.diaries.get_diary_by_id import GetDiaryByIdUseCase
from bzero.application.use_cases.diaries.get_today_diary import GetTodayDiaryUseCase
from bzero.presentation.api.dependencies import (
    CurrentDiaryService,
    CurrentJWTPayload,
    CurrentPointTransactionService,
    CurrentTicketService,
    CurrentUserService,
    DBSession,
)
from bzero.presentation.schemas.common import DataResponse
from bzero.presentation.schemas.diary import CreateDiaryRequest, DiaryListResponse, DiaryResponse


router = APIRouter(prefix="/diaries", tags=["diaries"])


@router.post(
    "",
    response_model=DataResponse[DiaryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="일기 작성",
    description="일기를 작성하고 포인트를 지급합니다 (50P, 하루 1회).",
)
async def create_diary(
    request: CreateDiaryRequest,
    session: DBSession,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    diary_service: CurrentDiaryService,
    ticket_service: CurrentTicketService,
    point_transaction_service: CurrentPointTransactionService,
) -> DataResponse[DiaryResponse]:
    """일기 작성.

    - 하루에 하나의 일기만 작성 가능 (중복 시 409 Conflict)
    - 작성 시 50P 자동 지급 (하루 1회)
    - diary_date는 탑승 중인 티켓 기준 또는 자정 기준으로 자동 계산
    """
    result = await CreateDiaryUseCase(
        session=session,
        user_service=user_service,
        diary_service=diary_service,
        ticket_service=ticket_service,
        point_transaction_service=point_transaction_service,
    ).execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        content=request.content,
        mood=request.mood,
        title=request.title,
        city_id=request.city_id,
    )

    return DataResponse(data=DiaryResponse.create_from(result))


@router.get(
    "/today",
    response_model=DataResponse[DiaryResponse | None],
    summary="오늘 일기 조회",
    description="오늘 작성한 일기를 조회합니다.",
)
async def get_today_diary(
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    diary_service: CurrentDiaryService,
    ticket_service: CurrentTicketService,
) -> DataResponse[DiaryResponse | None]:
    """오늘 일기 조회.

    - 본인이 오늘 작성한 일기만 조회 가능
    - 일기가 없으면 data=None 반환
    - "오늘"은 탑승 중인 티켓 기준 또는 자정 기준으로 자동 계산
    """
    result = await GetTodayDiaryUseCase(user_service, diary_service, ticket_service).execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
    )

    return DataResponse(data=DiaryResponse.create_from(result) if result else None)


@router.get(
    "",
    response_model=DiaryListResponse,
    summary="일기 목록 조회",
    description="사용자의 일기 목록을 최신순으로 조회합니다.",
)
async def get_diaries(
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    diary_service: CurrentDiaryService,
    offset: Annotated[int, Query(ge=0, description="조회 시작 위치")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="조회할 최대 개수")] = 20,
) -> DiaryListResponse:
    """일기 목록 조회.

    - 본인이 작성한 일기만 조회 가능
    - diary_date 역순 정렬 (최신순)
    - pagination 지원 (기본값: offset=0, limit=20)
    """
    result = await GetDiariesUseCase(user_service, diary_service).execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        offset=offset,
        limit=limit,
    )

    return DiaryListResponse(
        diaries=[DiaryResponse.create_from(item) for item in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.get(
    "/{diary_id}",
    response_model=DataResponse[DiaryResponse],
    summary="일기 상세 조회",
    description="일기 ID로 특정 일기를 조회합니다.",
)
async def get_diary_by_id(
    diary_id: str,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    diary_service: CurrentDiaryService,
) -> DataResponse[DiaryResponse]:
    """일기 상세 조회.

    - 본인이 작성한 일기만 조회 가능 (다른 사용자 일기 조회 시 404)
    - 존재하지 않는 일기 조회 시 404
    """
    result = await GetDiaryByIdUseCase(user_service, diary_service).execute(
        diary_id=diary_id,
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
    )

    return DataResponse(data=DiaryResponse.create_from(result))
