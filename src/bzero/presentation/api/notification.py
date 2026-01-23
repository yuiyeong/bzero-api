from fastapi import APIRouter

from bzero.application.use_cases.notifications import (
    GetNotificationsUseCase,
    GetUnreadNotificationCountUseCase,
    MarkAllNotificationsAsReadUseCase,
    MarkNotificationAsReadUseCase,
)
from bzero.presentation.api.dependencies import (
    CurrentJWTPayload,
    CurrentNotificationService,
    CurrentUserService,
    DBSession,
)
from bzero.presentation.schemas.common import ListResponse, Pagination
from bzero.presentation.schemas.notification import NotificationResponse, UnreadCountResponse


router = APIRouter(prefix="/notifications", tags=["notification"])


@router.get(
    "",
    response_model=ListResponse[NotificationResponse],
    summary="내 알림 목록 조회",
    description="나의 알림 목록을 최신순으로 조회합니다.",
)
async def get_my_notifications(
    session: DBSession,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    notification_service: CurrentNotificationService,
    offset: int = 0,
    limit: int = 20,
) -> ListResponse[NotificationResponse]:
    use_case = GetNotificationsUseCase(session, notification_service, user_service)
    notifications, total = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        offset=offset,
        limit=limit,
    )

    return ListResponse(
        list=[NotificationResponse.create_from(n) for n in notifications],
        pagination=Pagination(total=total, offset=offset, limit=limit),
    )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="읽지 않은 알림 개수 조회",
    description="읽지 않은 알림의 전체 개수를 조회합니다.",
)
async def get_unread_count(
    session: DBSession,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    notification_service: CurrentNotificationService,
) -> UnreadCountResponse:
    use_case = GetUnreadNotificationCountUseCase(session, notification_service, user_service)
    count = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
    )

    return UnreadCountResponse(count=count)


@router.post(
    "/read-all",
    response_model=UnreadCountResponse,
    summary="전체 알림 읽음 처리",
    description="나의 모든 알림을 읽음 처리합니다.",
)
async def mark_all_as_read(
    session: DBSession,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    notification_service: CurrentNotificationService,
) -> UnreadCountResponse:
    use_case = MarkAllNotificationsAsReadUseCase(session, notification_service, user_service)
    updated_count = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
    )

    # 읽음 처리 후 남은 안 읽은 개수는 0개일 것임 (혹은 트랜잭션 격리에 따라 다를 수 있지만 여기선 처리된 개수 반환보단 그냥 0 리턴이 맞을지도? 하지만 스키마가 count라 updated_count 리턴)
    # 기획적으로 "읽음 처리된 개수"를 반환할지 "남은 안 읽은 개수"를 반환할지 정해야 함.
    # 보통 API 응답은 "성공" 위주. 여기선 updated_count 반환. Client는 이를 보고 뱃지를 0으로 만듦.
    return UnreadCountResponse(count=updated_count)


@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="알림 읽음 처리",
    description="특정 알림을 읽음 처리합니다.",
)
async def mark_as_read(
    notification_id: str,
    session: DBSession,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    notification_service: CurrentNotificationService,
) -> NotificationResponse:
    use_case = MarkNotificationAsReadUseCase(session, notification_service, user_service)
    notification = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        notification_id=notification_id,
    )

    return NotificationResponse.create_from(notification)
