from billiard.einfo import ExceptionInfo
from celery import Task

from bzero.core.database import get_sync_db_session
from bzero.core.loggers import background_logger
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.task_failure_log_model import TaskFailureLogModel
from bzero.infrastructure.repositories.task_failure_log import SqlAlchemyTaskFailureLogRepository


logger = background_logger()


class FailoverTask(Task):
    # 태스크 실행이 완전히 끝난 후에 ACK(승인)를 보내기
    # 기본적으로 Celery는 워커가 태스크를 받자마자(실행 완료 전에) 브로커에게 "나 이거 받았어, 지워도 돼(ACK)"라고 신호를 보냄
    acks_late = True

    # task_acks_late=True와 함께 쓰이며,
    # 워커 프로세스가 태스크를 처리하다가 알 수 없는 이유로 사라졌을 때(SIGKILL 등),
    # 해당 태스크를 대기열(Queue)로 다시 돌려보냄(Re-queue).
    reject_on_worker_lost = True

    def on_failure(
        self, exc: Exception | None, task_id: str, args: tuple | None, kwargs: dict | None, einfo: ExceptionInfo | None
    ) -> None:
        """
        최종 실패 시 DB에 로그를 남깁니다.
        """
        task_name = self.name
        logger.error(f"[{task_name}] Task failed permanently. ID: {task_id}, Error: {exc!s}")

        try:
            error_message = str(exc) if exc else None
            traceback_contents = str(einfo) if einfo else None
            safe_args = list(args) if args else None
            safe_kwargs = dict(kwargs) if kwargs else None

            with get_sync_db_session() as session:
                repository = SqlAlchemyTaskFailureLogRepository(session)

                model = TaskFailureLogModel(
                    log_id=Id().value,
                    task_id=task_id,
                    task_name=task_name,
                    args=safe_args,
                    kwargs=safe_kwargs,
                    error_message=error_message,
                    traceback=traceback_contents,
                )

                repository.create(model)
                session.commit()
        except Exception as db_error:
            logger.critical(f"[{task_name}] Failed to save task failure log. Error: {db_error!s}]")

        super().on_failure(exc, task_id, args, kwargs, einfo)
