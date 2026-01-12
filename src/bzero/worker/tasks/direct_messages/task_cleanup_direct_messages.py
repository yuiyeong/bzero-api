"""만료된 DM 삭제 태스크.

만료 시간(설정값, 기본 3일)이 지난 Direct Message를 영구 삭제(Hard Delete)하는 배치 작업입니다.
Celery Beat에 의해 매일 아침 6시에 자동으로 실행됩니다.
"""

from datetime import datetime

from celery import shared_task
from sqlalchemy.exc import OperationalError

from bzero.core.database import get_sync_db_session
from bzero.core.loggers import background_logger
from bzero.core.settings import get_settings
from bzero.domain.services.direct_message import DirectMessageSyncService
from bzero.infrastructure.repositories.direct_message import SqlAlchemyDirectMessageSyncRepository
from bzero.worker.tasks.base import FailoverTask
from bzero.worker.tasks.names import CLEANUP_DIRECT_MESSAGES_TASK_NAME


logger = background_logger()


@shared_task(
    name=CLEANUP_DIRECT_MESSAGES_TASK_NAME,
    base=FailoverTask,
    autoretry_for=(OperationalError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def task_cleanup_direct_messages() -> dict:
    """만료된 DM을 삭제하는 태스크.

    expires_at < 현재 시간 조건을 만족하는 메시지를 영구 삭제합니다.
    매일 아침 6시에 Celery Beat에 의해 자동 실행됩니다.

    Returns:
        처리 결과를 담은 딕셔너리:
        - deleted_count: 삭제된 메시지 개수
        - result: "success" 또는 "failed; {에러메시지}"
    """
    logger.info("[task_cleanup_direct_messages] Start cleanup of expired DMs")

    error_message: str | None = None
    deleted_count = 0

    with get_sync_db_session() as session:
        try:
            # 1. 서비스 인스턴스 생성
            dm_service = DirectMessageSyncService(
                dm_sync_repository=SqlAlchemyDirectMessageSyncRepository(session),
            )

            # 2. 만료된 메시지 삭제 (현재 시간 기준)
            settings = get_settings()
            now = datetime.now(settings.timezone)
            deleted_count = dm_service.delete_expired_messages(now)

            # 3. 커밋
            session.commit()

            logger.info(f"[task_cleanup_direct_messages] Deleted {deleted_count} expired DMs")

        except Exception as e:
            session.rollback()
            error_message = str(e)
            logger.error(f"[task_cleanup_direct_messages] Error cleaning up DMs: {error_message}")
            raise e

    return {
        "deleted_count": deleted_count,
        "result": f"failed; {error_message}" if error_message else "success",
    }
