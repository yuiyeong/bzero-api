"""만료된 메시지 삭제 태스크.

만료 시간(3일)이 지난 채팅 메시지를 soft delete 처리하는 배치 작업입니다.
Celery Beat에 의해 매일 자정에 자동으로 실행됩니다.
"""

from datetime import datetime

from celery import shared_task
from sqlalchemy.exc import OperationalError

from bzero.core.database import get_sync_db_session
from bzero.core.loggers import background_logger
from bzero.core.settings import get_settings
from bzero.domain.services.chat_message_sync import ChatMessageSyncService
from bzero.infrastructure.repositories.chat_message import SqlAlchemyChatMessageSyncRepository
from bzero.worker.tasks.base import FailoverTask
from bzero.worker.tasks.names import DELETE_EXPIRED_MESSAGES_TASK_NAME


logger = background_logger()


@shared_task(
    name=DELETE_EXPIRED_MESSAGES_TASK_NAME,
    base=FailoverTask,
    autoretry_for=(OperationalError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def task_delete_expired_messages() -> dict:
    """만료된 메시지를 삭제하는 태스크.

    expires_at < 현재 시간 조건을 만족하는 메시지를 soft delete 처리합니다.
    매일 자정에 Celery Beat에 의해 자동 실행됩니다.

    Returns:
        처리 결과를 담은 딕셔너리:
        - deleted_count: 삭제된 메시지 개수
        - result: "success" 또는 "failed; {에러메시지}"
    """
    logger.info("[task_delete_expired_messages] Start deleting expired messages")

    error_message: str | None = None
    deleted_count = 0

    with get_sync_db_session() as session:
        try:
            # 1. 서비스 인스턴스 생성
            chat_message_service = ChatMessageSyncService(
                chat_message_sync_repository=SqlAlchemyChatMessageSyncRepository(session),
            )

            # 2. 만료된 메시지 삭제 (현재 시간 기준)
            settings = get_settings()
            now = datetime.now(settings.timezone)
            deleted_count = chat_message_service.delete_expired_messages(now)

            # 3. 커밋
            session.commit()

            logger.info(f"[task_delete_expired_messages] Deleted {deleted_count} expired messages")

        except Exception as e:
            session.rollback()
            error_message = str(e)
            logger.error(f"[task_delete_expired_messages] Error deleting expired messages: {error_message}")
            raise e

    return {
        "deleted_count": deleted_count,
        "result": f"failed; {error_message}" if error_message else "success",
    }
