"""일기 관련 API 엔드포인트."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, status
from zoneinfo import ZoneInfo

from bzero.application.use_cases.diaries.create_diary import CreateDiaryUseCase
from bzero.application.use_cases.diaries.get_diaries import GetDiariesUseCase
from bzero.application.use_cases.diaries.get_diary_by_id import GetDiaryByIdUseCase
from bzero.application.use_cases.diaries.get_today_diary import GetTodayDiaryUseCase
from bzero.presentation.api.dependencies import (
    CurrentDiaryService,
    CurrentJWTPayload,
    CurrentPointTransactionService,
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
    diary_service: CurrentDiaryService,
    point_transaction_service: CurrentPointTransactionService,
) -> DataResponse[DiaryResponse]:
    """일기 작성.

    - 하루에 하나의 일기만 작성 가능 (중복 시 409 Conflict)
    - 작성 시 50P 자동 지급 (하루 1회)
    - diary_date는 서버 시간 기준 오늘 날짜로 자동 설정
    """
    user_id = jwt_payload["sub"]
    today = date.today()

    result = await CreateDiaryUseCase(
        session=session,
        diary_service=diary_service,
        point_transaction_service=point_transaction_service,
    ).execute(
        user_id=user_id,
        content=request.content,
        mood=request.mood,
        diary_date=today,
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
    diary_service: CurrentDiaryService,
) -> DataResponse[DiaryResponse | None]:
    """오늘 일기 조회.

    - 본인이 오늘 작성한 일기만 조회 가능
    - 일기가 없으면 data=None 반환
    """
    user_id = jwt_payload["sub"]
    today = date.today()

    result = await GetTodayDiaryUseCase(diary_service).execute(user_id=user_id, today=today)

    return DataResponse(data=DiaryResponse.create_from(result) if result else None)


@router.get(
    "",
    response_model=DiaryListResponse,
    summary="일기 목록 조회",
    description="사용자의 일기 목록을 최신순으로 조회합니다.",
)
async def get_diaries(
    jwt_payload: CurrentJWTPayload,
    diary_service: CurrentDiaryService,
    offset: Annotated[int, Query(ge=0, description="조회 시작 위치")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="조회할 최대 개수")] = 20,
) -> DiaryListResponse:
    """일기 목록 조회.

    - 본인이 작성한 일기만 조회 가능
    - diary_date 역순 정렬 (최신순)
    - pagination 지원 (기본값: offset=0, limit=20)
    """
    user_id = jwt_payload["sub"]

    results, total = await GetDiariesUseCase(diary_service).execute(
        user_id=user_id,
        offset=offset,
        limit=limit,
    )

    return DiaryListResponse(
        diaries=[DiaryResponse.create_from(result) for result in results],
        total=total,
        offset=offset,
        limit=limit,
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
    diary_service: CurrentDiaryService,
) -> DataResponse[DiaryResponse]:
    """일기 상세 조회.

    - 본인이 작성한 일기만 조회 가능 (다른 사용자 일기 조회 시 404)
    - 존재하지 않는 일기 조회 시 404
    """
    user_id = jwt_payload["sub"]

    result = await GetDiaryByIdUseCase(diary_service).execute(
        diary_id=diary_id,
        user_id=user_id,
    )

    return DataResponse(data=DiaryResponse.create_from(result))
