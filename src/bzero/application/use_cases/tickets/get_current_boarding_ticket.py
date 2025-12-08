from bzero.application.results import TicketResult
from bzero.domain.errors import NotFoundTicketError
from bzero.domain.services import TicketService, UserService
from bzero.domain.value_objects import AuthProvider, TicketStatus


class GetCurrentBoardingTicketUseCase:
    def __init__(
        self,
        user_service: UserService,
        ticket_service: TicketService,
    ):
        self._user_service = user_service
        self._ticket_service = ticket_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
    ) -> TicketResult:
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )
        tickets, _ = await self._ticket_service.get_all_tickets_by_user_id_and_status(
            user_id=user.user_id, status=TicketStatus.BOARDING, limit=1
        )

        if not tickets:
            raise NotFoundTicketError

        return TicketResult.create_from(tickets[0])
