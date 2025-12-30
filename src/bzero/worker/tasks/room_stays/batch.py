from datetime import datetime, timedelta

from celery import shared_task

from bzero.core.database import get_sync_session_factory
from bzero.core.loggers import background_logger
from bzero.core.settings import get_settings
from bzero.domain.services.room_stay import NotificationSyncService, RoomStaySyncService
from bzero.infrastructure.repositories.notification import SqlAlchemyNotificationSyncRepository
from bzero.infrastructure.repositories.room_stay import SqlAlchemyRoomStaySyncRepository


logger = background_logger()


@shared_task(name="bzero.worker.tasks.room_stays.task_auto_checkout_batch")
def task_auto_checkout_batch() -> None:
    """만료된 숙박을 자동으로 체크아웃 처리하는 배치 태스크.

    10분마다 실행되며, 만료된 숙박 건을 조회하여 체크아웃 처리합니다.
    Lock 등을 통해 동시성 문제를 제어합니다.
    """
    logger.info("Starting task_auto_checkout_batch")
    settings = get_settings()
    session_factory = get_sync_session_factory()
    processed_count = 0

    with session_factory() as session:
        room_stay_repo = SqlAlchemyRoomStaySyncRepository(session)
        service = RoomStaySyncService(room_stay_repo, settings.timezone)

        # 1. 대상 조회 (Chunking: 1000건)
        # 만료 시간 < 현재 시간 인 건들
        ids = room_stay_repo.find_ids_due_for_checkout(limit=1000)
        logger.info(f"Checking out {len(ids)} stays...")

        for room_stay_id in ids:
            try:
                # 2. 개별 트랜잭션으로 처리 (하나 실패해도 전체 롤백되지 않도록)
                with session.begin_nested():
                    if service.checkout_if_expired(room_stay_id):
                        processed_count += 1
                session.commit()
            except Exception as e:
                session.rollback()
                logger.exception(f"Error checking out room_stay_id={room_stay_id}: {e}")

    logger.info(f"Finished task_auto_checkout_batch. Processed: {processed_count}")


@shared_task(name="bzero.worker.tasks.room_stays.task_send_checkout_reminder_batch")
def task_send_checkout_reminder_batch() -> None:
    """체크아웃 리마인더 알림을 발송하는 배치 태스크.

    10분마다 실행되며, 체크아웃 1시간 전인 숙박 건에 대해 알림을 발송합니다.
    발송 후 is_checkout_reminder_sent 플래그를 True로 설정합니다.
    """
    logger.info("Starting task_send_checkout_reminder_batch")
    settings = get_settings()
    session_factory = get_sync_session_factory()
    processed_count = 0

    with session_factory() as session:
        room_stay_repo = SqlAlchemyRoomStaySyncRepository(session)
        notification_repo = SqlAlchemyNotificationSyncRepository(session)

        # CheckoutSyncService 대신 NotificationSyncService와 RoomStay Repo 직접 사용
        notification_service = NotificationSyncService(notification_repo)

        # 1. 대상 조회
        # 현재 시간 < 만료 시간 <= 현재 시간 + 1시간 AND is_checkout_reminder_sent = False
        ids = room_stay_repo.find_ids_due_for_reminder(limit=1000)
        logger.info(f"Sending reminders for {len(ids)} stays...")

        for room_stay_id in ids:
            try:
                with session.begin_nested():
                    # 2. Lock & Check
                    room_stay = room_stay_repo.find_by_room_stay_id(room_stay_id, with_for_update=True)
                    if not room_stay:
                        continue

                    if room_stay.is_checkout_reminder_sent:
                        continue

                    # Double Check Time (이미 연장되었거나 만료되었는지)
                    now = datetime.now(settings.timezone)
                    one_hour_later = now + timedelta(hours=1)

                    # 만약 체크아웃 시간이 1시간 이내가 아니라면 (연장됨) 스킵
                    # 또는 이미 지났다면 (이미 지났지만 체크아웃 안된 상태 -> 리마인더 보다는 체크아웃 대상이나, 일단 여기서도 보낼지 여부는 기획 따름.
                    # 보통 만료 전 알림이므로, 만료되지 않았고 1시간 이내인 경우만)
                    if not (now < room_stay.scheduled_check_out_at <= one_hour_later):
                        continue

                    # 3. 알림 생성
                    notification_service.create_checkout_reminder(
                        user_id=room_stay.user_id,
                        message=f"체크아웃 시간이 임박했습니다. {room_stay.scheduled_check_out_at.strftime('%H:%M')}까지 체크아웃해주세요.",
                    )

                    # 4. 플래그 업데이트
                    room_stay.is_checkout_reminder_sent = True
                    room_stay_repo.update(room_stay)
                    processed_count += 1

                session.commit()
            except Exception as e:
                session.rollback()
                logger.exception(f"Error sending reminder specific room_stay_id={room_stay_id}: {e}")

    logger.info(f"Finished task_send_checkout_reminder_batch. Processed: {processed_count}")
