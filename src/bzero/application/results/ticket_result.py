from dataclasses import dataclass
from datetime import datetime

from bzero.domain.entities import Ticket


@dataclass
class CitySnapshotResult:
    city_id: str
    name: str
    theme: str
    image_url: str | None
    description: str | None


@dataclass
class AirshipSnapshotResult:
    airship_id: str
    name: str
    image_url: str | None
    description: str


@dataclass
class TicketResult:
    ticket_id: str
    user_id: str
    city_snapshot: CitySnapshotResult
    airship_snapshot: AirshipSnapshotResult
    ticket_number: str
    cost_points: int
    status: str
    departure_datetime: datetime
    arrival_datetime: datetime
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_from(cls, entity: Ticket) -> "TicketResult":
        city_snapshot_result = CitySnapshotResult(
            city_id=entity.city_snapshot.city_id.to_hex(),
            name=entity.city_snapshot.name,
            theme=entity.city_snapshot.theme,
            image_url=entity.city_snapshot.image_url,
            description=entity.city_snapshot.description,
        )
        airship_snapshot_result = AirshipSnapshotResult(
            airship_id=entity.airship_snapshot.airship_id.to_hex(),
            name=entity.airship_snapshot.name,
            image_url=entity.airship_snapshot.image_url,
            description=entity.airship_snapshot.description,
        )
        return cls(
            ticket_id=entity.ticket_id.to_hex(),
            user_id=entity.user_id.to_hex(),
            city_snapshot=city_snapshot_result,
            airship_snapshot=airship_snapshot_result,
            ticket_number=entity.ticket_number,
            cost_points=entity.cost_points,
            status=entity.status.value,
            departure_datetime=entity.departure_datetime,
            arrival_datetime=entity.arrival_datetime,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
