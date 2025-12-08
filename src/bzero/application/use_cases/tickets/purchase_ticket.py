from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results import TicketResult
from bzero.domain.services import AirshipService, CityService, PointTransactionService, TicketService, UserService
from bzero.domain.value_objects import AuthProvider, Id, TransactionReason, TransactionReference


class PurchaseTicketUseCase:
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
        city_id: str,
        airship_id: str,
    ) -> TicketResult:
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )
        city = await self._city_service.get_active_city_by_id(Id.from_hex(city_id))
        airship = await self._airship_service.get_active_airship_by_id(Id.from_hex(airship_id))
        ticket = await self._ticket_service.purchase_ticket(user, city, airship)

        await self._point_transaction_service.spend_by(
            user=user,
            amount=ticket.cost_points,
            reason=TransactionReason.TICKET,
            reference_type=TransactionReference.TICKETS,
            reference_id=ticket.ticket_id,
        )

        await self._session.commit()

        return TicketResult.create_from(ticket)
