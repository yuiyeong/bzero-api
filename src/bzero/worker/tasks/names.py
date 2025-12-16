# Celery Task 이름 상수
# Task 정의와 send_task 호출 양쪽에서 사용

COMPLETE_TICKET_TASK_NAME = "bzero.worker.tasks.tickets.task_complete_ticket"
CHECK_IN_TASK_NAME = "bzero.worker.tasks.room_stays.task_check_in"
