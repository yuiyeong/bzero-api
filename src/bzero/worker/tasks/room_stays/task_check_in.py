from celery import shared_task
from sqlalchemy.exc import OperationalError

from bzero.core.database import get_sync_db_session
from bzero.core.loggers import background_logger
from bzero.core.settings import get_settings
from bzero.domain.errors import (
    InvalidTicketStatusError,
    NotFoundGuestHouseError,
    NotFoundTicketError,
    RoomCapacityLockError,
)
from bzero.domain.services.guest_house import GuestHouseSyncService
from bzero.domain.services.room import RoomSyncService
from bzero.domain.services.room_stay import RoomStaySyncService
from bzero.domain.services.ticket import TicketSyncService
from bzero.domain.value_objects import Id
from bzero.infrastructure.repositories.guest_house import SqlAlchemyGuestHouseSyncRepository
from bzero.infrastructure.repositories.room import SqlAlchemyRoomSyncRepository
from bzero.infrastructure.repositories.room_stay import SqlAlchemyRoomStaySyncRepository
from bzero.infrastructure.repositories.ticket import SqlAlchemyTicketSyncRepository
from bzero.worker.tasks import CHECK_IN_TASK_NAME
from bzero.worker.tasks.base import FailoverTask


logger = background_logger()


@shared_task(
    name=CHECK_IN_TASK_NAME,
    base=FailoverTask,
    autoretry_for=(
        OperationalError,
        RoomCapacityLockError,
    ),  # DB 연결 오류 등 일시적 오류 시 재시도
    retry_backoff=True,  # 재시도 간격을 점진적으로 늘림 (기본: 1초, 2초, 4초...)
    retry_kwargs={"max_retries": 3},  # 최대 3회 재시도
)
def task_check_in(ticket_id: str) -> dict:
    """도시에 도착했을 때, guest_house 의 한 room 에 check-in 하는 태스크"""
    logger.info(f"[task_check_in] Start with a ticket({ticket_id})")

    dict_to_return = {"ticket_id": ticket_id}

    error_message: str | None = None
    timezone = get_settings().timezone
    with get_sync_db_session() as session:
        ticket_service = TicketSyncService(
            ticket_sync_repository=SqlAlchemyTicketSyncRepository(session),
        )
        guest_house_service = GuestHouseSyncService(
            guest_house_sync_repository=SqlAlchemyGuestHouseSyncRepository(session),
        )
        room_service = RoomSyncService(
            room_sync_repository=SqlAlchemyRoomSyncRepository(session),
            timezone=timezone,
        )
        room_stay_service = RoomStaySyncService(
            room_stay_sync_repository=SqlAlchemyRoomStaySyncRepository(session),
            timezone=timezone,
        )

        try:
            ticket = ticket_service.get_ticket_by_id(Id.from_hex(ticket_id))
            guest_house = guest_house_service.get_guest_house_in_city(ticket.city_snapshot.city_id)
            room = room_service.get_or_create_room_for_update(guest_house.guest_house_id)
            updated_room = room_service.occupy_room(room)
            room_stay = room_stay_service.assign_room(ticket, updated_room)

            session.commit()
            dict_to_return["room_stay_id"] = room_stay.room_stay_id.to_hex()
        except (NotFoundTicketError, InvalidTicketStatusError, NotFoundGuestHouseError) as e:
            # 비즈니스 예외: 로깅 후 결과 반환 (재시도 안함)
            session.rollback()
            error_message = e.code.value
            logger.warning(f"[task_check_in] Business logic error in task_check_in: {error_message}")

    dict_to_return["result"] = f"failed; {error_message}" if error_message else "success"

    return dict_to_return
