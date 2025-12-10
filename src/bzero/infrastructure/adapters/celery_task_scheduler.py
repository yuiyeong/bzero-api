from datetime import datetime

from bzero.domain.ports import TaskScheduler
from bzero.worker.app import bzero_celery_app
from bzero.worker.tasks import COMPLETE_TICKET_TASK_NAME


class CeleryTaskScheduler(TaskScheduler):
    def schedule_ticket_completion(self, ticket_id: str, eta: datetime) -> None:
        """티켓 완료 작업을 Celery를 통해 예약합니다."""
        bzero_celery_app.send_task(
            COMPLETE_TICKET_TASK_NAME,
            args=[ticket_id],
            eta=eta,
        )
