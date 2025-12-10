from typing import Annotated

from fastapi import APIRouter, Query

from bzero.application.use_cases.tickets.get_current_boarding_ticket import GetCurrentBoardingTicketUseCase
from bzero.application.use_cases.tickets.get_ticket_detail import GetTicketDetailUseCase
from bzero.application.use_cases.tickets.get_tickets_by_user import GetTicketsByUserUseCase
from bzero.application.use_cases.tickets.purchase_ticket import PurchaseTicketUseCase
from bzero.presentation.api.dependencies import (
    CurrentAirshipService,
    CurrentCityService,
    CurrentJWTPayload,
    CurrentPointTransactionService,
    CurrentTaskScheduler,
    CurrentTicketService,
    CurrentUserService,
    DBSession,
)
from bzero.presentation.schemas.common import DataResponse, ListResponse, Pagination
from bzero.presentation.schemas.ticket import PurchaseTicketRequest, TicketResponse


router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post(
    "",
    response_model=DataResponse[TicketResponse],
    summary="티켓 구매",
    description="비행선 티켓을 구매합니다.",
)
async def purchase_ticket(
    request: PurchaseTicketRequest,
    jwt_payload: CurrentJWTPayload,
    session: DBSession,
    user_service: CurrentUserService,
    city_service: CurrentCityService,
    airship_service: CurrentAirshipService,
    ticket_service: CurrentTicketService,
    point_transaction_service: CurrentPointTransactionService,
    task_scheduler: CurrentTaskScheduler,
) -> DataResponse[TicketResponse]:
    """티켓을 구매합니다.

    Args:
        request: 티켓 구매 요청 (city_id, airship_id)
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        session: 데이터베이스 세션
        user_service: 사용자 도메인 서비스
        city_service: 도시 도메인 서비스
        airship_service: 비행선 도메인 서비스
        ticket_service: 티켓 도메인 서비스
        point_transaction_service: 포인트 트랜잭션 도메인 서비스
        task_scheduler: 태스크 스케줄러

    Returns:
        TicketResponse: 구매한 티켓 정보
    """
    use_case = PurchaseTicketUseCase(
        session=session,
        user_service=user_service,
        city_service=city_service,
        airship_service=airship_service,
        ticket_service=ticket_service,
        point_transaction_service=point_transaction_service,
        task_scheduler=task_scheduler,
    )
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        city_id=request.city_id,
        airship_id=request.airship_id,
    )
    return DataResponse(data=TicketResponse.create_from(result))


@router.get(
    "/mine",
    response_model=ListResponse[TicketResponse],
    summary="내 티켓 목록 조회",
    description="내가 구매한 티켓 목록을 조회합니다.",
)
async def get_my_tickets(
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    ticket_service: CurrentTicketService,
    offset: Annotated[int, Query(ge=0, description="조회 시작 위치")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="조회할 최대 개수")] = 20,
) -> ListResponse[TicketResponse]:
    """내 티켓 목록을 조회합니다.

    Args:
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        user_service: 사용자 도메인 서비스
        ticket_service: 티켓 도메인 서비스
        offset: 조회 시작 위치 (기본값: 0)
        limit: 조회할 최대 개수 (기본값: 20, 최대: 100)

    Returns:
        ListResponse[TicketResponse]: 티켓 목록과 페이지네이션 정보
    """
    use_case = GetTicketsByUserUseCase(
        user_service=user_service,
        ticket_service=ticket_service,
    )
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        offset=offset,
        limit=limit,
    )
    return ListResponse(
        list=[TicketResponse.create_from(ticket) for ticket in result.items],
        pagination=Pagination(total=result.total, offset=result.offset, limit=result.limit),
    )


@router.get(
    "/mine/boarding",
    response_model=DataResponse[TicketResponse],
    summary="현재 탑승 중인 티켓 조회",
    description="현재 탑승 중인(boarding 상태) 티켓을 조회합니다.",
)
async def get_current_boarding_ticket(
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    ticket_service: CurrentTicketService,
) -> DataResponse[TicketResponse]:
    """현재 탑승 중인 티켓을 조회합니다.

    Args:
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        user_service: 사용자 도메인 서비스
        ticket_service: 티켓 도메인 서비스

    Returns:
        TicketResponse: 현재 탑승 중인 티켓 정보

    Raises:
        NotFoundTicketError: 탑승 중인 티켓이 없는 경우
    """
    use_case = GetCurrentBoardingTicketUseCase(
        user_service=user_service,
        ticket_service=ticket_service,
    )
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
    )
    return DataResponse(data=TicketResponse.create_from(result))


@router.get(
    "/{ticket_id}",
    response_model=DataResponse[TicketResponse],
    summary="티켓 상세 조회",
    description="특정 티켓의 상세 정보를 조회합니다.",
)
async def get_ticket_detail(
    ticket_id: str,
    jwt_payload: CurrentJWTPayload,
    user_service: CurrentUserService,
    ticket_service: CurrentTicketService,
) -> DataResponse[TicketResponse]:
    """티켓 상세 정보를 조회합니다.

    Args:
        ticket_id: 티켓 ID (UUID v7 hex)
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)
        user_service: 사용자 도메인 서비스
        ticket_service: 티켓 도메인 서비스

    Returns:
        TicketResponse: 티켓 상세 정보
    """
    use_case = GetTicketDetailUseCase(
        user_service=user_service,
        ticket_service=ticket_service,
    )
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
        ticket_id=ticket_id,
    )
    return DataResponse(data=TicketResponse.create_from(result))
