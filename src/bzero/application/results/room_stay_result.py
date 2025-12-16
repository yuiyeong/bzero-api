from dataclasses import dataclass
from datetime import datetime

from bzero.domain.entities import RoomStay


@dataclass(frozen=True)
class RoomStayResult:
    room_stay_id: str
    user_id: str
    city_id: str
    guest_house_id: str
    room_id: str
    ticket_id: str
    status: str
    check_in_at: datetime
    scheduled_check_out_at: datetime
    actual_check_out_at: datetime | None
    extension_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_from(cls, entity: RoomStay) -> "RoomStayResult":
        return cls(
            room_stay_id=entity.room_stay_id.to_hex(),
            user_id=entity.user_id.to_hex(),
            city_id=entity.city_id.to_hex(),
            guest_house_id=entity.guest_house_id.to_hex(),
            room_id=entity.room_id.to_hex(),
            ticket_id=entity.ticket_id.to_hex(),
            status=entity.status.value,
            check_in_at=entity.check_in_at,
            scheduled_check_out_at=entity.scheduled_check_out_at,
            actual_check_out_at=entity.actual_check_out_at,
            extension_count=entity.extension_count,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
