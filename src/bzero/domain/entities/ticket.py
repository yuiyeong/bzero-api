from dataclasses import dataclass
from datetime import datetime

from bzero.domain.errors import InvalidTicketStatusError
from bzero.domain.value_objects import AirshipSnapshot, CitySnapshot, Id, TicketStatus


@dataclass
class Ticket:
    ticket_id: Id
    user_id: Id
    city_snapshot: CitySnapshot
    airship_snapshot: AirshipSnapshot
    ticket_number: str
    cost_points: int
    status: TicketStatus
    departure_datetime: datetime
    arrival_datetime: datetime
    created_at: datetime
    updated_at: datetime

    def consume(self) -> None:
        if self.status != TicketStatus.PURCHASED:
            raise InvalidTicketStatusError

        self.status = TicketStatus.BOARDING

    def complete(self) -> None:
        if self.status != TicketStatus.BOARDING:
            raise InvalidTicketStatusError

        self.status = TicketStatus.COMPLETED

    def cancel(self) -> None:
        if self.status != TicketStatus.PURCHASED:
            raise InvalidTicketStatusError

        self.status = TicketStatus.CANCELLED

    @classmethod
    def create(
        cls,
        user_id: Id,
        city_snapshot: CitySnapshot,
        airship_snapshot: AirshipSnapshot,
        cost_points: int,
        departure_datetime: datetime,
        arrival_datetime: datetime,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Ticket":
        ticket_id = Id()
        ticket_number = cls.generate_ticket_number(
            user_id=user_id, ticket_id=ticket_id, departure_datetime=departure_datetime
        )
        return cls(
            ticket_id=ticket_id,
            user_id=user_id,
            city_snapshot=city_snapshot,
            airship_snapshot=airship_snapshot,
            ticket_number=ticket_number,
            cost_points=cost_points,
            status=TicketStatus.PURCHASED,
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def generate_ticket_number(cls, user_id: Id, ticket_id: Id, departure_datetime: datetime) -> str:
        return f"B0-{departure_datetime.year}-{user_id.extract_time()}{ticket_id.extract_time()}"
