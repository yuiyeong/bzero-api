from abc import ABC, abstractmethod

from bzero.domain.entities.ticket import Ticket
from bzero.domain.value_objects import Id, TicketStatus


class TicketRepository(ABC):
    @abstractmethod
    async def create(self, ticket: Ticket) -> Ticket:
        pass

    @abstractmethod
    async def update(self, ticket: Ticket) -> Ticket:
        pass

    @abstractmethod
    async def find_by_id(self, ticket_id: Id) -> Ticket | None:
        pass

    @abstractmethod
    async def find_all_by_user_id(
        self,
        user_id: Id,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Ticket]:
        pass

    @abstractmethod
    async def find_all_by_user_id_and_status(
        self,
        user_id: Id,
        status: TicketStatus,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Ticket]:
        pass

    @abstractmethod
    async def count_by(self, user_id: Id | None = None, status: TicketStatus | None = None) -> int:
        pass
