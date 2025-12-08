from dataclasses import dataclass
from enum import Enum

from bzero.domain.value_objects import Id


class TicketStatus(str, Enum):
    PURCHASED = "purchased"
    BOARDING = "boarding"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class CitySnapshot:
    city_id: Id
    name: str
    theme: str
    image_url: str | None
    description: str | None
    base_cost_points: int
    base_duration_hours: int


@dataclass(frozen=True)
class AirshipSnapshot:
    airship_id: Id
    name: str
    image_url: str | None
    description: str
    cost_factor: int
    duration_factor: int
