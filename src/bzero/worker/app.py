"""Celery 워커 애플리케이션.

B0 프로젝트의 백그라운드 태스크를 처리하는 Celery 워커를 설정합니다.
Redis를 브로커와 결과 백엔드로 사용하며, 동기 DB 연결을 관리합니다.

사용법:
    celery -A bzero.worker.app worker --loglevel=info
"""

from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init, worker_process_shutdown

from bzero.core.database import close_sync_db_connection, setup_sync_db_connection
from bzero.core.loggers import background_logger, setup_loggers
from bzero.core.settings import get_settings


def create_celery_app() -> Celery:
    """Celery 애플리케이션을 생성하고 설정합니다.

    Returns:
        설정이 완료된 Celery 인스턴스
    """
    settings = get_settings()

    setup_loggers(settings)

    celery_app = Celery(
        "bzero",
        broker=settings.celery.broker_url,
        backend=settings.celery.result_backend,
    )

    celery_app.conf.update(
        # 타임존 설정
        timezone=settings.timezone,
        enable_utc=True,
        # 태스크 직렬화 설정
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        result_expires=3600,  # 1시간 후 결과 삭제
        # 워커 설정
        worker_prefetch_multiplier=4,  # 한 번에 가져올 태스크 수
        worker_max_tasks_per_child=1000,  # 워커 프로세스 재시작 주기
        # 태스크 추적 설정
        task_track_started=True,  # 태스크 시작 상태 추적
        task_time_limit=30 * 60,  # 30분 하드 타임아웃
        task_soft_time_limit=15 * 60,  # 15분 소프트 타임아웃
        # Kombu 연결 버그 수정
        broker_connection_retry_on_startup=True,
        # Celery Beat 스케줄 설정
        beat_schedule={
            "delete-expired-messages-daily": {
                "task": "bzero.worker.tasks.chat_messages.task_delete_expired_messages",
                "schedule": crontab(hour=0, minute=0),  # 매일 자정에 실행
            },
        },
    )

    # bzero.worker.tasks 모듈에서 태스크 자동 발견
    celery_app.autodiscover_tasks(["bzero.worker.tasks"])

    return celery_app


# Celery 앱 인스턴스 (모듈 레벨에서 생성)
bzero_celery_app = create_celery_app()


@worker_process_init.connect
def init_worker(**_):
    """워커 프로세스 초기화 시 동기 DB 연결을 설정합니다.

    Celery 워커가 시작될 때 호출되며, 동기 SQLAlchemy 세션을 초기화합니다.
    이 세션은 워커 프로세스 수명 동안 유지됩니다.
    """
    settings = get_settings()
    logger = background_logger()
    logger.info("Celery Worker 시작(process init)")
    try:
        setup_sync_db_connection(settings)
        logger.info("Done setup_sync_db_connection...")
    except Exception as e:
        logger.exception(f"동기 DB 초기화 실패(process init); {e!s}")


@worker_process_shutdown.connect
def shutdown_worker(**_):
    """워커 프로세스 종료 시 동기 DB 연결을 정리합니다.

    Celery 워커가 종료될 때 호출되며, 동기 SQLAlchemy 엔진을 정리합니다.
    """
    logger = background_logger()
    try:
        close_sync_db_connection()
        logger.info("Done close_sync_db_connection...")
    except Exception as e:
        logger.exception(f"동기 DB 종료 처리 중 오류: {e!s}")
