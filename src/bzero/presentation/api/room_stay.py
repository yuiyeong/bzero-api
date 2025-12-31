from fastapi import APIRouter, HTTPException, status

from bzero.application.use_cases.room_stays import CheckoutUseCase, ExtendStayUseCase, GetCurrentStayUseCase
from bzero.domain.errors import (
    ForbiddenRoomForUserError,
    InsufficientBalanceError,
    InvalidStayStatusError,
    NoActiveStayError,
)
from bzero.presentation.api.dependencies import (
    CurrentCheckoutService,
    CurrentJWTPayload,
    CurrentRoomStayService,
    CurrentStayExtensionService,
    CurrentUserService,
    DBSession,
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
    session: DBSession,
    user_service: CurrentUserService,
    room_stay_service: CurrentRoomStayService,
    stay_extension_service: CurrentStayExtensionService,
) -> DataResponse[RoomStayResponse]:
    """현재 체류를 연장합니다."""
    use_case = ExtendStayUseCase(
        session=session,
        user_service=user_service,
        room_stay_service=room_stay_service,
        stay_extension_service=stay_extension_service,
    )

    try:
        result = await use_case.execute(
            provider=jwt_payload.provider,
            provider_user_id=jwt_payload.provider_user_id,
        )
        return DataResponse(data=RoomStayResponse.create_from(result))
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient points") from e
    except (NoActiveStayError, InvalidStayStatusError) as e:
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
    session: DBSession,
    user_service: CurrentUserService,
    room_stay_service: CurrentRoomStayService,
    checkout_service: CurrentCheckoutService,
) -> DataResponse[RoomStayResponse]:
    """현재 체류를 체크아웃합니다."""
    use_case = CheckoutUseCase(
        session=session,
        user_service=user_service,
        room_stay_service=room_stay_service,
        checkout_service=checkout_service,
    )

    try:
        result = await use_case.execute(
            provider=jwt_payload.provider,
            provider_user_id=jwt_payload.provider_user_id,
        )
        return DataResponse(data=RoomStayResponse.create_from(result))
    except NoActiveStayError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active stay found") from e
    except ForbiddenRoomForUserError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from e
