from bzero.application.results import TicketResult
from bzero.domain.services import TicketService, UserService
from bzero.domain.value_objects import AuthProvider, Id


class GetTicketDetailUseCase:
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
        ticket_id: str,
    ) -> TicketResult:
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )
        ticket = await self._ticket_service.get_ticket_by_id(Id.from_hex(ticket_id), user.user_id)
        return TicketResult.create_from(ticket)
