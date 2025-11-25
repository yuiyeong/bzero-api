"""사용자 관련 API 엔드포인트."""

from fastapi import APIRouter, status

from bzero.application.use_cases.users.create_user import CreateUserUseCase
from bzero.application.use_cases.users.get_me import GetMeUseCase
from bzero.application.use_cases.users.update_user import UpdateUserUseCase
from bzero.presentation.api.dependencies import (
    CurrentJWTPayload,
    CurrentPointTransactionService,
    CurrentUserService,
    DBSession,
)
from bzero.presentation.schemas.common import DataResponse
from bzero.presentation.schemas.user import UpdateUserRequest, UserResponse


router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/me",
    response_model=DataResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="신규 사용자 등록",
    description="Supabase 인증 후 첫 로그인 시 호출해야합니다. GET /users/me에서 404를 받은 경우에만 호출합니다.",
)
async def create_user(
    jwt_payload: CurrentJWTPayload,
    session: DBSession,
    user_service: CurrentUserService,
    point_transaction_service: CurrentPointTransactionService,
) -> DataResponse[UserResponse]:
    """신규 사용자 등록.

    - JWT 토큰에서 사용자 정보(sub, email)를 추출하여 사용자 생성
    - 초기 포인트 1000P 지급
    - nickname, profile은 None (온보딩에서 설정)
    """
    result = await CreateUserUseCase(session, user_service, point_transaction_service).execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        email=jwt_payload.email,
    )

    return DataResponse(data=UserResponse.create_from(result))


@router.get(
    "/me",
    response_model=DataResponse[UserResponse],
    summary="현재 사용자 정보 조회",
    description="JWT 토큰으로 인증된 사용자 본인의 정보를 조회합니다.",
)
async def get_me(
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
) -> DataResponse[UserResponse]:
    """현재 로그인한 사용자 정보 조회."""
    result = await GetMeUseCase(user_service).execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
    )
    return DataResponse(data=UserResponse.create_from(result))


@router.patch(
    "/me",
    response_model=DataResponse[UserResponse],
    summary="사용자 프로필 수정",
    description="닉네임과 프로필 이모지를 수정합니다. 온보딩 완료 시에도 사용됩니다.",
)
async def update_user(
    request: UpdateUserRequest,
    jwt_payload: CurrentJWTPayload,
    session: DBSession,
    user_service: CurrentUserService,
) -> DataResponse[UserResponse]:
    """사용자 프로필 수정.

    - 닉네임: 2-10자, 한글/영문/숫자만 허용
    - 프로필 이모지: 1-2자
    """
    result = await UpdateUserUseCase(session, user_service).execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        nickname=request.nickname,
        emoji=request.profile_emoji,
    )
    return DataResponse(data=UserResponse.create_from(result))
