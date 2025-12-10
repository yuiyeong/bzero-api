"""티켓 취소 유스케이스.

사용자가 구매한 티켓을 취소하고 포인트를 환불받는 비즈니스 로직을 담당합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results import TicketResult
from bzero.domain.services import AirshipService, CityService, PointTransactionService, TicketService, UserService
from bzero.domain.value_objects import AuthProvider, Id, TransactionReason, TransactionReference


class CancelTicketUseCase:
    """티켓 취소 유스케이스.

    사용자가 구매한 티켓을 취소하고 사용한 포인트를 환불받습니다.

    비즈니스 규칙:
        - 자신의 티켓만 취소 가능 (소유권 검증)
        - PURCHASED 상태인 티켓만 취소 가능
        - 취소 시 구매에 사용한 포인트 전액 환불
        - 취소된 티켓은 CANCELLED 상태로 변경

    Note:
        현재 구매 즉시 BOARDING 상태로 전환되는 구조이므로,
        실제로 취소 가능한 시점이 제한적일 수 있습니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        city_service: CityService,
        airship_service: AirshipService,
        ticket_service: TicketService,
        point_transaction_service: PointTransactionService,
    ):
        self._session = session
        self._user_service = user_service
        self._city_service = city_service
        self._airship_service = airship_service
        self._ticket_service = ticket_service
        self._point_transaction_service = point_transaction_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
        ticket_id: str,
    ) -> TicketResult:
        """티켓 취소를 실행합니다.

        Args:
            provider: 인증 제공자 (예: "supabase")
            provider_user_id: 인증 제공자의 사용자 ID
            ticket_id: 취소할 티켓 ID (hex 문자열)

        Returns:
            취소된 티켓 정보 (CANCELLED 상태)

        Raises:
            NotFoundUserError: 사용자를 찾을 수 없는 경우
            NotFoundTicketError: 티켓을 찾을 수 없는 경우
            ForbiddenTicketError: 다른 사용자의 티켓을 취소하려는 경우
            InvalidTicketStatusError: 취소 불가능한 상태의 티켓인 경우
        """
        # 1. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        # 2. 티켓 취소 (소유권 및 상태 검증 포함)
        ticket = await self._ticket_service.cancel(user_id=user.user_id, ticket_id=Id.from_hex(ticket_id))

        # 3. 포인트 환불
        await self._point_transaction_service.earn_by(
            user=user,
            amount=ticket.cost_points,
            reason=TransactionReason.REFUND,
            reference_type=TransactionReference.TICKETS,
            reference_id=ticket.ticket_id,
            description="티켓 취소로 인한 환불",
        )

        # 4. 트랜잭션 커밋
        await self._session.commit()

        return TicketResult.create_from(ticket)
