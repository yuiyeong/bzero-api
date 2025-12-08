from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results import TicketResult
from bzero.domain.services import AirshipService, CityService, PointTransactionService, TicketService, UserService
from bzero.domain.value_objects import AuthProvider, Id, TransactionReason, TransactionReference


class CancelTicketUseCase:
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
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )
        ticket = await self._ticket_service.cancel(user_id=user.user_id, ticket_id=Id.from_hex(ticket_id))

        await self._point_transaction_service.earn_by(
            user=user,
            amount=ticket.cost_points,
            reason=TransactionReason.REFUND,
            reference_type=TransactionReference.TICKETS,
            reference_id=ticket.ticket_id,
            description="티켓 취소로 인한 환불",
        )

        await self._session.commit()

        return TicketResult.create_from(ticket)
