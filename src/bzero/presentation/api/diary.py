"""일기 관련 API 엔드포인트."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from bzero.application.use_cases.diaries.create_diary import CreateDiaryUseCase
from bzero.application.use_cases.diaries.get_diaries import GetDiariesUseCase
from bzero.application.use_cases.diaries.get_diary_by_id import GetDiaryByIdUseCase
from bzero.application.use_cases.diaries.get_today_diary import GetTodayDiaryUseCase
from bzero.domain.value_objects import Id
from bzero.presentation.api.dependencies import (
    CurrentDiaryService,
    CurrentJWTPayload,
    CurrentPointTransactionService,
    CurrentUserService,
)
from bzero.presentation.schemas.common import DataResponse
from bzero.presentation.schemas.diary import CreateDiaryRequest, DiaryListResponse, DiaryResponse

router = APIRouter(prefix="/diaries", tags=["diaries"])


@router.post(
    "",
    response_model=DataResponse[DiaryResponse],
    status_code=201,
    summary="일기 작성",
    description="일기를 작성하고 50P를 지급합니다. (하루 1회)",
)
async def create_diary(
    request: CreateDiaryRequest,
    jwt_payload: CurrentJWTPayload,
    diary_service: CurrentDiaryService,
    point_transaction_service: CurrentPointTransactionService,
    user_service: CurrentUserService,
) -> DataResponse[DiaryResponse]:
    """일기 작성.

    - 하루 1회 작성 가능 (user_id, diary_date 유일 제약)
    - 작성 시 50P 지급
    - 중복 작성 시 409 Conflict 반환

    Args:
        request: 일기 작성 요청 (title, content, mood, diary_date, city_id)

    Returns:
        생성된 일기 정보
    """
    # 사용자 조회 (인증된 사용자)
    user = await user_service.get_user_by_provider(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
    )

    # UseCase 실행
    use_case = CreateDiaryUseCase(diary_service, point_transaction_service)
    result = await use_case.execute(
        user_id=user.user_id,
        title=request.title,
        content=request.content,
        mood=request.mood,
        diary_date=request.diary_date,
        city_id=Id(request.city_id) if request.city_id else None,
    )

    return DataResponse(data=DiaryResponse.from_result(result))


@router.get(
    "/today",
    response_model=DataResponse[DiaryResponse],
    summary="오늘 일기 조회",
    description="오늘 작성한 일기를 조회합니다.",
)
async def get_today_diary(
    jwt_payload: CurrentJWTPayload,
    diary_service: CurrentDiaryService,
    user_service: CurrentUserService,
) -> DataResponse[DiaryResponse]:
    """오늘 일기 조회.

    - 오늘 날짜의 일기만 조회
    - 본인만 조회 가능
    - 없으면 404 반환

    Returns:
        오늘 작성한 일기 정보
    """
    # 사용자 조회
    user = await user_service.get_user_by_provider(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
    )

    # UseCase 실행
    use_case = GetTodayDiaryUseCase(diary_service)
    result = await use_case.execute(user_id=user.user_id, today=date.today())

    return DataResponse(data=DiaryResponse.from_result(result))


@router.get(
    "",
    response_model=DiaryListResponse,
    summary="일기 목록 조회",
    description="사용자의 일기 목록을 최신순으로 조회합니다.",
)
async def get_diaries(
    jwt_payload: CurrentJWTPayload,
    diary_service: CurrentDiaryService,
    user_service: CurrentUserService,
    offset: Annotated[int, Query(ge=0, description="조회 시작 위치")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="조회할 최대 개수")] = 20,
) -> DiaryListResponse:
    """일기 목록 조회.

    - 본인 일기만 조회
    - diary_date 역순 정렬 (최신순)
    - pagination 지원 (기본값: offset=0, limit=20)

    Args:
        offset: 조회 시작 위치 (기본값: 0)
        limit: 조회할 최대 개수 (기본값: 20, 최대: 100)

    Returns:
        일기 목록 및 전체 개수
    """
    # 사용자 조회
    user = await user_service.get_user_by_provider(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
    )

    # UseCase 실행
    use_case = GetDiariesUseCase(diary_service)
    results, total = await use_case.execute(user_id=user.user_id, offset=offset, limit=limit)

    return DiaryListResponse(
        diaries=[DiaryResponse.from_result(result) for result in results],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{diary_id}",
    response_model=DataResponse[DiaryResponse],
    summary="일기 상세 조회",
    description="일기 ID로 일기를 조회합니다. (본인만 조회 가능)",
)
async def get_diary_by_id(
    diary_id: str,
    jwt_payload: CurrentJWTPayload,
    diary_service: CurrentDiaryService,
    user_service: CurrentUserService,
) -> DataResponse[DiaryResponse]:
    """일기 상세 조회.

    - 본인만 조회 가능 (다른 사용자 접근 시 403 반환)
    - 없으면 404 반환

    Args:
        diary_id: 일기 ID (UUID 문자열)

    Returns:
        일기 상세 정보
    """
    # 사용자 조회
    user = await user_service.get_user_by_provider(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
    )

    # UseCase 실행
    use_case = GetDiaryByIdUseCase(diary_service)
    result = await use_case.execute(diary_id=Id(diary_id), current_user_id=user.user_id)

    return DataResponse(data=DiaryResponse.from_result(result))
