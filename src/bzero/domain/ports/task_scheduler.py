from abc import ABC, abstractmethod
from datetime import datetime


class TaskScheduler(ABC):
    @abstractmethod
    def schedule_ticket_completion(self, ticket_id: str, eta: datetime) -> None:
        """티켓 완료 작업을 예약합니다."""
