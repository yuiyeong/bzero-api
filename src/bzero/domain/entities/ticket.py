"""비행선 티켓 엔티티.

사용자가 도시로 여행하기 위해 구매하는 비행선 티켓을 나타냅니다.
티켓은 구매 → 탑승 → 완료 또는 취소의 생명주기를 가집니다.
"""

from dataclasses import dataclass
from datetime import datetime

from bzero.domain.errors import AlreadyCompletedTicketError, InvalidTicketStatusError
from bzero.domain.value_objects import AirshipSnapshot, CitySnapshot, Id, TicketStatus


@dataclass
class Ticket:
    """비행선 티켓 엔티티.

    Attributes:
        ticket_id: 티켓 고유 식별자 (UUID v7)
        user_id: 티켓 소유자의 사용자 ID
        city_snapshot: 구매 시점의 도시 정보 스냅샷
        airship_snapshot: 구매 시점의 비행선 정보 스냅샷
        ticket_number: 티켓 번호 (예: "B0-2025-abc123def456")
        cost_points: 티켓 구매에 사용된 포인트
        status: 티켓 상태 (PURCHASED, BOARDING, COMPLETED, CANCELLED)
        departure_datetime: 출발 일시
        arrival_datetime: 도착 예정 일시
        created_at: 생성 일시
        updated_at: 수정 일시
    """

    ticket_id: Id
    user_id: Id
    city_snapshot: CitySnapshot
    airship_snapshot: AirshipSnapshot
    ticket_number: str
    cost_points: int
    status: TicketStatus
    departure_datetime: datetime
    arrival_datetime: datetime
    created_at: datetime
    updated_at: datetime

    @property
    def is_completed(self) -> bool:
        return self.status == TicketStatus.COMPLETED

    def consume(self) -> None:
        """티켓을 사용하여 탑승 상태로 변경합니다.

        Raises:
            InvalidTicketStatusError: 티켓이 PURCHASED 상태가 아닌 경우
        """
        if self.status != TicketStatus.PURCHASED:
            raise InvalidTicketStatusError

        self.status = TicketStatus.BOARDING

    def complete(self) -> None:
        """여행을 완료하고 티켓을 완료 상태로 변경합니다.

        Raises:
            InvalidTicketStatusError: 티켓이 BOARDING 상태가 아닌 경우
        """
        if self.status == TicketStatus.PURCHASED:
            raise InvalidTicketStatusError
        if self.status in (TicketStatus.COMPLETED, TicketStatus.CANCELLED):
            raise AlreadyCompletedTicketError

        self.status = TicketStatus.COMPLETED

    def cancel(self) -> None:
        """티켓을 취소합니다.

        Raises:
            InvalidTicketStatusError: 티켓이 PURCHASED 상태가 아닌 경우
        """
        if self.status != TicketStatus.PURCHASED:
            raise InvalidTicketStatusError

        self.status = TicketStatus.CANCELLED

    @classmethod
    def create(
        cls,
        user_id: Id,
        city_snapshot: CitySnapshot,
        airship_snapshot: AirshipSnapshot,
        cost_points: int,
        departure_datetime: datetime,
        arrival_datetime: datetime,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Ticket":
        """새 티켓을 생성합니다.

        Args:
            user_id: 티켓 소유자의 사용자 ID
            city_snapshot: 도시 정보 스냅샷
            airship_snapshot: 비행선 정보 스냅샷
            cost_points: 티켓 비용 (포인트)
            departure_datetime: 출발 일시
            arrival_datetime: 도착 예정 일시
            created_at: 생성 일시
            updated_at: 수정 일시

        Returns:
            새로 생성된 Ticket 엔티티 (PURCHASED 상태)
        """
        ticket_id = Id()
        ticket_number = cls.generate_ticket_number(
            user_id=user_id, ticket_id=ticket_id, departure_datetime=departure_datetime
        )
        return cls(
            ticket_id=ticket_id,
            user_id=user_id,
            city_snapshot=city_snapshot,
            airship_snapshot=airship_snapshot,
            ticket_number=ticket_number,
            cost_points=cost_points,
            status=TicketStatus.PURCHASED,
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def generate_ticket_number(cls, user_id: Id, ticket_id: Id, departure_datetime: datetime) -> str:
        """티켓 번호를 생성합니다.

        형식: "B0-{년도}-{사용자ID타임스탬프}{티켓ID타임스탬프}"

        Args:
            user_id: 사용자 ID
            ticket_id: 티켓 ID
            departure_datetime: 출발 일시

        Returns:
            생성된 티켓 번호 문자열
        """
        return f"B0-{departure_datetime.year}-{user_id.extract_time()}{ticket_id.extract_time()}"
