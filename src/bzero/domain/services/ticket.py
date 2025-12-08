from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bzero.domain.entities import Airship, City, Ticket, User
from bzero.domain.errors import (
    ForbiddenTicketError,
    InsufficientBalanceError,
    InvalidAirshipStatusError,
    InvalidCityStatusError,
    NotFoundTicketError,
)
from bzero.domain.repositories.ticket import TicketRepository
from bzero.domain.value_objects import Id, TicketStatus


class TicketService:
    def __init__(self, ticket_repository: TicketRepository, timezone: ZoneInfo):
        self._ticket_repository = ticket_repository
        self._timezone = timezone

    async def purchase_ticket(self, user: User, city: City, airship: Airship) -> Ticket:
        total_cost = city.base_cost_points * airship.cost_factor
        total_duration = city.base_duration_hours * airship.duration_factor

        if user.current_points.less_than(total_cost):
            raise InsufficientBalanceError

        if not city.is_active:
            raise InvalidCityStatusError

        if not airship.is_active:
            raise InvalidAirshipStatusError

        departure_datetime = datetime.now(self._timezone)
        arrival_datetime = departure_datetime + timedelta(hours=total_duration)
        ticket = Ticket.create(
            user_id=user.user_id,
            city_snapshot=city.snapshot(),
            airship_snapshot=airship.snapshot(),
            cost_points=total_cost,
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            created_at=departure_datetime,
            updated_at=departure_datetime,
        )
        ticket.consume()
        return await self._ticket_repository.create(ticket)

    async def complete(self, user_id: Id, ticket_id: Id) -> Ticket:
        ticket = await self.get_ticket_by_id(
            ticket_id=ticket_id,
            user_id=user_id,
        )
        ticket.complete()
        return await self._ticket_repository.update(ticket)

    async def cancel(self, user_id: Id, ticket_id: Id) -> Ticket:
        ticket = await self.get_ticket_by_id(
            ticket_id=ticket_id,
            user_id=user_id,
        )
        ticket.cancel()
        return await self._ticket_repository.update(ticket)

    async def get_ticket_by_id(self, ticket_id: Id, user_id: Id | None = None) -> Ticket:
        ticket = await self._ticket_repository.find_by_id(ticket_id)
        if ticket is None:
            raise NotFoundTicketError

        if user_id and ticket.user_id != user_id:
            raise ForbiddenTicketError

        return ticket

    async def get_all_tickets_by_user_id(
        self, user_id: Id, offset: int = 0, limit: int = 100
    ) -> tuple[list[Ticket], int]:
        tickets = await self._ticket_repository.find_all_by_user_id(
            user_id=user_id,
            offset=offset,
            limit=limit,
        )
        total = await self._ticket_repository.count_by(user_id=user_id)
        return tickets, total

    async def get_all_tickets_by_user_id_and_status(
        self, user_id: Id, status: TicketStatus, offset: int = 0, limit: int = 100
    ) -> tuple[list[Ticket], int]:
        tickets = await self._ticket_repository.find_all_by_user_id_and_status(
            user_id=user_id,
            status=status,
            offset=offset,
            limit=limit,
        )
        total = await self._ticket_repository.count_by(user_id=user_id, status=status)
        return tickets, total
