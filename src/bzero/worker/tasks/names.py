# Celery Task 이름 상수
# Task 정의와 send_task 호출 양쪽에서 사용

COMPLETE_TICKET_TASK_NAME = "bzero.worker.tasks.tickets.task_complete_ticket"
CHECK_IN_TASK_NAME = "bzero.worker.tasks.room_stays.task_check_in"
DELETE_EXPIRED_MESSAGES_TASK_NAME = "bzero.worker.tasks.chat_messages.task_delete_expired_messages"
CLEANUP_DIRECT_MESSAGES_TASK_NAME = "bzero.worker.tasks.direct_messages.task_cleanup_direct_messages"
