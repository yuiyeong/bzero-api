from celery import shared_task
from sqlalchemy.exc import OperationalError

from bzero.core.database import get_sync_db_session
from bzero.core.loggers import background_logger
from bzero.domain.errors import AlreadyCompletedTicketError, BeZeroError
from bzero.domain.repositories.ticket import TicketSyncRepository
from bzero.domain.services.ticket import TicketSyncService
from bzero.domain.value_objects import Id
from bzero.infrastructure.repositories.ticket import SqlAlchemyTicketSyncRepository
from bzero.worker.app import bzero_celery_app
from bzero.worker.tasks import CHECK_IN_TASK_NAME
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
def task_complete_ticket(ticket_id: str) -> dict:
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
    logger.info(f"[task_complete_ticket] Start a ticket({ticket_id})")

    error_message: str | None = None

    with get_sync_db_session() as session:
        ticket_repository: TicketSyncRepository = SqlAlchemyTicketSyncRepository(session)
        ticket_service: TicketSyncService = TicketSyncService(ticket_repository)

        try:
            ticket = ticket_service.complete(Id.from_hex(ticket_id))

            session.commit()

            logger.info(f"[complete_ticket_task] Done complete_ticket_task of {ticket.ticket_id.to_hex()}")
            bzero_celery_app.send_task(CHECK_IN_TASK_NAME, args=[ticket.ticket_id.to_hex()])
        except AlreadyCompletedTicketError:
            # 이미 처리된 ticket 으로 Nothing to do(멱등성 보장)
            return {"ticket_id": ticket_id, "result": "success"}
        except BeZeroError as e:
            session.rollback()
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
