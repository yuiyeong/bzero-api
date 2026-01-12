"""티켓 배치 처리 태스크.

도착 시간이 지난 BOARDING 티켓을 완료 처리하고 체크인하는 배치 태스크입니다.
Celery Beat으로 1분마다 실행됩니다.
"""

from celery import shared_task

from bzero.core.database import get_sync_session_factory
from bzero.core.loggers import background_logger
from bzero.core.settings import get_settings
from bzero.domain.errors import (
    AlreadyCompletedTicketError,
    BeZeroError,
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
from bzero.worker.tasks.names import COMPLETE_TICKETS_AND_CHECK_IN_BATCH_TASK_NAME


logger = background_logger()


@shared_task(name=COMPLETE_TICKETS_AND_CHECK_IN_BATCH_TASK_NAME)
def task_complete_tickets_and_check_in_batch() -> dict:
    """도착 시간이 지난 BOARDING 티켓을 완료 처리하고 체크인하는 배치 태스크.

    1분마다 실행되며, 다음 조건의 티켓을 조회하여 처리합니다:
    - status = BOARDING
    - arrival_datetime <= 현재 시간

    각 티켓에 대해:
    1. 티켓 상태를 COMPLETED로 변경
    2. 게스트하우스 룸에 체크인 (RoomStay 생성)

    Returns:
        처리 결과 딕셔너리:
        - processed: 성공 건수
        - failed: 실패 건수
        - total: 전체 대상 건수
    """
    logger.info("Starting task_complete_tickets_and_check_in_batch")

    settings = get_settings()
    session_factory = get_sync_session_factory()
    processed_count = 0
    failed_count = 0

    with session_factory() as session:
        ticket_repo = SqlAlchemyTicketSyncRepository(session)

        # 1. 대상 조회 (Chunking: 1000건)
        ids = ticket_repo.find_ids_due_for_completion(limit=1000)
        total_count = len(ids)
        logger.info(f"Found {total_count} tickets due for completion")

        for ticket_id in ids:
            try:
                # 2. 개별 트랜잭션으로 처리 (하나 실패해도 전체 롤백되지 않도록)
                with session.begin_nested():
                    result = _process_single_ticket(session, ticket_id, settings.timezone)
                    if result:
                        processed_count += 1
                session.commit()
            except AlreadyCompletedTicketError:
                # 멱등성: 이미 처리된 티켓은 스킵 (성공으로 간주)
                session.rollback()
                logger.debug(f"Ticket already completed: {ticket_id.to_hex()}")
            except BeZeroError as e:
                session.rollback()
                failed_count += 1
                logger.warning(f"Business error processing ticket_id={ticket_id.to_hex()}: {e.code.value}")
            except Exception as e:
                session.rollback()
                failed_count += 1
                logger.exception(f"Error processing ticket_id={ticket_id.to_hex()}: {e}")

    result = {
        "processed": processed_count,
        "failed": failed_count,
        "total": total_count,
    }
    logger.info(f"Finished task_complete_tickets_and_check_in_batch: {result}")
    return result


def _process_single_ticket(session, ticket_id: Id, timezone) -> bool:
    """단일 티켓을 완료 처리하고 체크인합니다.

    Args:
        session: DB 세션
        ticket_id: 티켓 ID
        timezone: 시간대

    Returns:
        처리 성공 여부

    Raises:
        AlreadyCompletedTicketError: 이미 완료된 티켓인 경우
        NotFoundTicketError: 티켓을 찾을 수 없는 경우
        InvalidTicketStatusError: 티켓 상태가 올바르지 않은 경우
        NotFoundGuestHouseError: 게스트하우스를 찾을 수 없는 경우
    """
    # 서비스 인스턴스 생성
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
        room_sync_repository=SqlAlchemyRoomSyncRepository(session),
        timezone=timezone,
    )

    # 1. 티켓 완료 처리 (BOARDING → COMPLETED)
    ticket = ticket_service.complete(ticket_id)

    # 2. 게스트하우스 룸 체크인
    guest_house = guest_house_service.get_guest_house_in_city(ticket.city_snapshot.city_id)
    room = room_service.get_or_create_room_for_update(guest_house.guest_house_id)
    updated_room = room_service.occupy_room(room)
    room_stay_service.assign_room(ticket, updated_room)

    logger.info(f"Completed ticket and checked in: {ticket_id.to_hex()}")
    return True
