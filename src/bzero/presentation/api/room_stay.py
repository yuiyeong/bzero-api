from fastapi import APIRouter, HTTPException, status

from bzero.application.use_cases.room_stays.get_current_stay import GetCurrentStayUseCase
from bzero.domain.errors import (
    ForbiddenRoomForUserError,
    InsufficientBalanceError,
    InvalidStayStatusError,
    NoActiveStayError,
)
from bzero.domain.value_objects import AuthProvider
from bzero.presentation.api.dependencies import (
    CurrentCheckoutService,
    CurrentJWTPayload,
    CurrentRoomStayService,
    CurrentStayExtensionService,
    CurrentUserService,
)
from bzero.presentation.schemas.common import DataResponse, ErrorResponse
from bzero.presentation.schemas.room_stay import RoomStayResponse


router = APIRouter(prefix="/room-stays", tags=["room-stays"])


@router.get(
    "/current",
    response_model=DataResponse[RoomStayResponse] | None,
    summary="현재 체류 조회",
    description="현재 활성(CHECKED_IN) 체류 정보를 조회합니다.",
)
async def get_current_stay(
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    room_stay_service: CurrentRoomStayService,
) -> DataResponse[RoomStayResponse] | None:
    """현재 체류 정보를 조회합니다."""
    use_case = GetCurrentStayUseCase(
        user_service=user_service,
        room_stay_service=room_stay_service,
    )
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
    )
    if result is None:
        return None
    return DataResponse(data=RoomStayResponse.create_from(result))


@router.post(
    "/current/extend",
    response_model=DataResponse[RoomStayResponse],
    summary="체류 연장",
    description="현재 체류를 24시간 연장합니다. 300 포인트가 차감됩니다.",
    responses={
        400: {"model": ErrorResponse, "description": "포인트 부족 또는 잘못된 상태"},
        404: {"model": ErrorResponse, "description": "활성 체류 없음"},
    },
)
async def extend_current_stay(
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    room_stay_service: CurrentRoomStayService,
    stay_extension_service: CurrentStayExtensionService,
) -> DataResponse[RoomStayResponse]:
    """현재 체류를 연장합니다."""
    # 1. 사용자 조회 (ID 획득)
    user = await user_service.find_user_by_provider_and_provider_user_id(
        provider=AuthProvider(jwt_payload.provider),
        provider_user_id=jwt_payload.provider_user_id,
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # 2. 현재 체류 조회
    # (Concurrency: 서비스 내부에서 Lock 걸어 다시 조회하므로 여기서는 ID만 필요하지만,
    # 존재 여부 빠른 확인을 위해 조회. or directly call extend if we knew ID.
    # But API is /current/extend so we must lookup first.)
    current_stay = await room_stay_service.get_checked_in_by_user_id(user.user_id)
    if not current_stay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active stay found")

    try:
        # 3. 연장 실행
        updated_stay = await stay_extension_service.extend_stay(
            room_stay_id=current_stay.room_stay_id,
            user_id=user.user_id,
        )
        return DataResponse(data=RoomStayResponse.create_from(updated_stay))
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient points") from e
    except (NoActiveStayError, InvalidStayStatusError) as e:
        # 락 획득 후 상태가 변경되었을 수 있음
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No active stay found or invalid status"
        ) from e
    except ForbiddenRoomForUserError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from e


@router.post(
    "/current/checkout",
    response_model=DataResponse[RoomStayResponse],
    summary="체크아웃",
    description="현재 체류를 체크아웃합니다.",
    responses={
        404: {"model": ErrorResponse, "description": "활성 체류 없음"},
    },
)
async def checkout_current_stay(
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    room_stay_service: CurrentRoomStayService,
    checkout_service: CurrentCheckoutService,
) -> DataResponse[RoomStayResponse]:
    """현재 체류를 체크아웃합니다."""
    # 1. 사용자 조회
    user = await user_service.find_user_by_provider_and_provider_user_id(
        provider=AuthProvider(jwt_payload.provider),
        provider_user_id=jwt_payload.provider_user_id,
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # 2. 현재 체류 조회
    current_stay = await room_stay_service.get_checked_in_by_user_id(user.user_id)
    if not current_stay:
        # 이미 체크아웃 된 상태일 수도 있고, 없을 수도 있음.
        # 기획적으로 '현재 체크인 된 것이 없으면' 404가 맞음.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active stay found")

    try:
        # 3. 체크아웃 실행
        updated_stay = await checkout_service.checkout(
            room_stay_id=current_stay.room_stay_id,
            user_id=user.user_id,
        )
        return DataResponse(data=RoomStayResponse.create_from(updated_stay))
    except NoActiveStayError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active stay found") from e
    except ForbiddenRoomForUserError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from e
