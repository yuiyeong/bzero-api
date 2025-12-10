"""티켓 관련 Celery 태스크.

비행선 여행 완료 처리 등 티켓 관련 백그라운드 작업을 정의합니다.
이 태스크들은 동기 DB 세션을 사용하여 처리됩니다.
"""

from celery import shared_task
from sqlalchemy.exc import OperationalError

from bzero.core.database import get_sync_db_session
from bzero.core.loggers import background_logger
from bzero.domain.errors import BeZeroError, NotFoundTicketError
from bzero.domain.repositories.ticket_sync import TicketSyncRepository
from bzero.domain.value_objects import Id, TicketStatus
from bzero.infrastructure.repositories.ticket_sync import SqlAlchemyTicketSyncRepository
from bzero.worker.tasks.base import FailoverTask
from bzero.worker.tasks.names import COMPLETE_TICKET_TASK_NAME


logger = background_logger()


@shared_task(
    name=COMPLETE_TICKET_TASK_NAME,
    base=FailoverTask,
    autoretry_for=(OperationalError,),  # DB 연결 오류 등 일시적 오류 시 재시도
    retry_backoff=True,  # 재시도 간격을 점진적으로 늘림 (기본: 1초, 2초, 4초...)
    retry_kwargs={"max_retries": 3},  # 최대 3회 재시도
)
def complete_ticket_task(ticket_id: str) -> dict:
    """비행선 여행을 완료 처리하는 태스크.

    티켓 상태를 BOARDING에서 COMPLETED로 변경합니다.
    도착 시간이 되면 스케줄러에 의해 자동으로 호출됩니다.

    Args:
        ticket_id: 완료 처리할 티켓 ID (hex 문자열)

    Returns:
        처리 결과를 담은 딕셔너리:
        - ticket_id: 처리된 티켓 ID
        - result: "success" 또는 "failed; {에러코드}"
    """
    logger.info(f"[complete_ticket_task] Start complete_ticket_task with: {ticket_id}")

    error_message: str | None = None

    with get_sync_db_session() as session:
        ticket_repository: TicketSyncRepository = SqlAlchemyTicketSyncRepository(session)

        try:
            ticket = ticket_repository.find_by_id(Id.from_hex(ticket_id))
            if ticket is None:
                raise NotFoundTicketError

            if ticket.status in (TicketStatus.COMPLETED, TicketStatus.CANCELLED):
                # Nothing to do(멱등성 보장)
                return {"ticket_id": ticket_id, "result": "success"}

            # BOARDING → COMPLETED 상태 변경
            ticket.complete()

            ticket_repository.update(ticket)

            session.commit()
            logger.info(f"[complete_ticket_task] Done complete_ticket_task of {ticket_id}")
        except BeZeroError as e:
            error_message = e.code.value
            logger.error(f"[complete_ticket_task] Business logic error in complete_ticket_task: {error_message}")
        except Exception as e:
            # 여기서는 로깅 후 예외를 다시 던져서 Celery가 처리하게 함
            logger.error(f"[complete_ticket_task] Unexpected error in complete_ticket_task: {e}")
            raise e
    return {
        "ticket_id": ticket_id,
        "result": f"failed; {error_message}" if error_message else "success",
    }
