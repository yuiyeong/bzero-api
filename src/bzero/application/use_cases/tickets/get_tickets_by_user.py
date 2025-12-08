from bzero.application.results import PaginatedResult, TicketResult
from bzero.domain.services import TicketService, UserService
from bzero.domain.value_objects import AuthProvider


class GetTicketsByUserUseCase:
    def __init__(
        self,
        user_service: UserService,
        ticket_service: TicketService,
    ):
        self._user_service = user_service
        self._ticket_service = ticket_service

    async def execute(
        self, provider: str, provider_user_id: str, offset: int, limit: int
    ) -> PaginatedResult[TicketResult]:
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )
        tickets, total = await self._ticket_service.get_all_tickets_by_user_id(
            user_id=user.user_id, offset=offset, limit=limit
        )
        items = [TicketResult.create_from(ticket) for ticket in tickets]
        return PaginatedResult(items=items, total=total, offset=offset, limit=limit)
