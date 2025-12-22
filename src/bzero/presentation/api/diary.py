"""일기 API 엔드포인트."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from bzero.application.use_cases.diaries.create_diary import CreateDiaryUseCase
from bzero.application.use_cases.diaries.delete_diary import DeleteDiaryUseCase
from bzero.application.use_cases.diaries.get_diaries_by_user import (
    GetDiariesByUserUseCase,
)
from bzero.application.use_cases.diaries.get_diary_detail import GetDiaryDetailUseCase
from bzero.application.use_cases.diaries.update_diary import UpdateDiaryUseCase
from bzero.presentation.api.dependencies import (
    CurrentDiaryService,
    CurrentJWTPayload,
    CurrentPointTransactionService,
    CurrentRoomStayService,
    CurrentUserService,
    DBSession,
)
from bzero.presentation.schemas.common import DataResponse
from bzero.presentation.schemas.diary import (
    CreateDiaryRequest,
    DiaryListResponse,
    DiaryResponse,
    UpdateDiaryRequest,
)


router = APIRouter(prefix="/diaries", tags=["diaries"])


@router.post(
    "",
    response_model=DataResponse[DiaryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="일기 작성",
    description="현재 체류 중인 게스트하우스에서 일기를 작성합니다. 체류당 1개의 일기만 작성 가능하며, 작성 시 50P가 지급됩니다.",
)
async def create_diary(
    request: CreateDiaryRequest,
    jwt_payload: CurrentJWTPayload,
    session: DBSession,
    user_service: CurrentUserService,
    room_stay_service: CurrentRoomStayService,
    diary_service: CurrentDiaryService,
    point_transaction_service: CurrentPointTransactionService,
) -> DataResponse[DiaryResponse]:
    """일기를 작성합니다.

    Args:
        request: 일기 생성 요청 (title, content, mood)
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        session: 데이터베이스 세션
        user_service: 사용자 도메인 서비스
        room_stay_service: 체류 도메인 서비스
        diary_service: 일기 도메인 서비스
        point_transaction_service: 포인트 트랜잭션 도메인 서비스

    Returns:
        DiaryResponse: 생성된 일기 정보
    """
    use_case = CreateDiaryUseCase(
        session=session,
        user_service=user_service,
        room_stay_service=room_stay_service,
        diary_service=diary_service,
        point_transaction_service=point_transaction_service,
    )
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        title=request.title,
        content=request.content,
        mood=request.mood.value,
    )
    return DataResponse(data=DiaryResponse.create_from(result))


@router.get(
    "",
    response_model=DiaryListResponse,
    summary="내 일기 목록 조회",
    description="내가 작성한 일기 목록을 조회합니다.",
)
async def get_my_diaries(
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    diary_service: CurrentDiaryService,
    offset: Annotated[int, Query(ge=0, description="조회 시작 위치")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="조회할 최대 개수")] = 20,
) -> DiaryListResponse:
    """내 일기 목록을 조회합니다.

    Args:
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        user_service: 사용자 도메인 서비스
        diary_service: 일기 도메인 서비스
        offset: 조회 시작 위치 (기본값: 0)
        limit: 조회할 최대 개수 (기본값: 20, 최대: 100)

    Returns:
        DiaryListResponse: 일기 목록과 페이지네이션 정보
    """
    use_case = GetDiariesByUserUseCase(
        user_service=user_service,
        diary_service=diary_service,
    )
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        limit=limit,
        offset=offset,
    )
    return DiaryListResponse(
        items=[DiaryResponse.create_from(diary) for diary in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.get(
    "/{diary_id}",
    response_model=DataResponse[DiaryResponse],
    summary="일기 상세 조회",
    description="특정 일기의 상세 정보를 조회합니다.",
)
async def get_diary_detail(
    diary_id: str,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    diary_service: CurrentDiaryService,
) -> DataResponse[DiaryResponse]:
    """일기 상세 정보를 조회합니다.

    Args:
        diary_id: 일기 ID (UUID v7 hex)
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        user_service: 사용자 도메인 서비스
        diary_service: 일기 도메인 서비스

    Returns:
        DiaryResponse: 일기 상세 정보
    """
    use_case = GetDiaryDetailUseCase(
        user_service=user_service,
        diary_service=diary_service,
    )
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        diary_id=diary_id,
    )
    return DataResponse(data=DiaryResponse.create_from(result))


@router.patch(
    "/{diary_id}",
    response_model=DataResponse[DiaryResponse],
    summary="일기 수정",
    description="일기의 제목, 내용, 감정을 수정합니다.",
)
async def update_diary(
    diary_id: str,
    request: UpdateDiaryRequest,
    jwt_payload: CurrentJWTPayload,
    session: DBSession,
    user_service: CurrentUserService,
    diary_service: CurrentDiaryService,
) -> DataResponse[DiaryResponse]:
    """일기를 수정합니다.

    Args:
        diary_id: 일기 ID (UUID v7 hex)
        request: 일기 수정 요청 (title, content, mood)
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        session: 데이터베이스 세션
        user_service: 사용자 도메인 서비스
        diary_service: 일기 도메인 서비스

    Returns:
        DiaryResponse: 수정된 일기 정보
    """
    use_case = UpdateDiaryUseCase(
        session=session,
        user_service=user_service,
        diary_service=diary_service,
    )
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        diary_id=diary_id,
        title=request.title,
        content=request.content,
        mood=request.mood.value,
    )
    return DataResponse(data=DiaryResponse.create_from(result))


@router.delete(
    "/{diary_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="일기 삭제",
    description="일기를 삭제합니다 (soft delete).",
)
async def delete_diary(
    diary_id: str,
    jwt_payload: CurrentJWTPayload,
    session: DBSession,
    user_service: CurrentUserService,
    diary_service: CurrentDiaryService,
) -> None:
    """일기를 삭제합니다.

    Args:
        diary_id: 일기 ID (UUID v7 hex)
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        session: 데이터베이스 세션
        user_service: 사용자 도메인 서비스
        diary_service: 일기 도메인 서비스
    """
    use_case = DeleteDiaryUseCase(
        session=session,
        user_service=user_service,
        diary_service=diary_service,
    )
    await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        diary_id=diary_id,
    )
