"""Ticket 엔티티 단위 테스트"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.entities.ticket import Ticket
from bzero.domain.errors import InvalidTicketStatusError
from bzero.domain.value_objects import AirshipSnapshot, CitySnapshot, Id, TicketStatus


class TestTicket:
    """Ticket 엔티티 단위 테스트"""

    @pytest.fixture
    def tz(self) -> ZoneInfo:
        """Seoul timezone"""
        return get_settings().timezone

    @pytest.fixture
    def sample_city_snapshot(self) -> CitySnapshot:
        """샘플 도시 스냅샷"""
        return CitySnapshot(
            city_id=Id(uuid7()),
            name="세렌시아",
            theme="관계",
            image_url="https://example.com/serencia.jpg",
            description="노을빛 항구 마을",
            base_cost_points=300,
            base_duration_hours=24,
        )

    @pytest.fixture
    def sample_airship_snapshot(self) -> AirshipSnapshot:
        """샘플 비행선 스냅샷"""
        return AirshipSnapshot(
            airship_id=Id(uuid7()),
            name="일반 비행선",
            image_url="https://example.com/normal.jpg",
            description="편안하고 여유로운 여행을 원하는 여행자를 위한 비행선",
            cost_factor=1,
            duration_factor=1,
        )

    def test_create_ticket(
        self, sample_city_snapshot: CitySnapshot, sample_airship_snapshot: AirshipSnapshot, tz: ZoneInfo
    ):
        """티켓을 생성할 수 있다"""
        # Given
        user_id = Id(uuid7())
        cost_points = 300
        departure_datetime = datetime.now(tz)
        arrival_datetime = departure_datetime + timedelta(hours=24)
        created_at = departure_datetime
        updated_at = departure_datetime

        # When
        ticket = Ticket.create(
            user_id=user_id,
            city_snapshot=sample_city_snapshot,
            airship_snapshot=sample_airship_snapshot,
            cost_points=cost_points,
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            created_at=created_at,
            updated_at=updated_at,
        )

        # Then
        assert ticket.ticket_id is not None
        assert ticket.user_id == user_id
        assert ticket.city_snapshot == sample_city_snapshot
        assert ticket.airship_snapshot == sample_airship_snapshot
        assert ticket.cost_points == cost_points
        assert ticket.status == TicketStatus.PURCHASED
        assert ticket.departure_datetime == departure_datetime
        assert ticket.arrival_datetime == arrival_datetime
        assert ticket.created_at == created_at
        assert ticket.updated_at == updated_at

    def test_create_ticket_generates_ticket_number(
        self, sample_city_snapshot: CitySnapshot, sample_airship_snapshot: AirshipSnapshot, tz: ZoneInfo
    ):
        """티켓 생성 시 티켓 번호가 자동 생성된다"""
        # Given
        user_id = Id(uuid7())
        departure_datetime = datetime.now(tz)
        arrival_datetime = departure_datetime + timedelta(hours=24)
        created_at = departure_datetime
        updated_at = departure_datetime

        # When
        ticket = Ticket.create(
            user_id=user_id,
            city_snapshot=sample_city_snapshot,
            airship_snapshot=sample_airship_snapshot,
            cost_points=300,
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            created_at=created_at,
            updated_at=updated_at,
        )

        # Then
        assert ticket.ticket_number is not None
        assert ticket.ticket_number.startswith(f"B0-{departure_datetime.year}-")

    def test_generate_ticket_number(self, tz: ZoneInfo):
        """티켓 번호를 생성할 수 있다"""
        # Given
        user_id = Id(uuid7())
        ticket_id = Id(uuid7())
        departure_datetime = datetime.now(tz)

        # When
        ticket_number = Ticket.generate_ticket_number(
            user_id=user_id,
            ticket_id=ticket_id,
            departure_datetime=departure_datetime,
        )

        # Then
        assert ticket_number.startswith(f"B0-{departure_datetime.year}-")
        assert len(ticket_number) > 10

    def test_consume_ticket_from_purchased_status(
        self, sample_city_snapshot: CitySnapshot, sample_airship_snapshot: AirshipSnapshot, tz: ZoneInfo
    ):
        """PURCHASED 상태의 티켓을 소비하여 BOARDING 상태로 변경할 수 있다"""
        # Given
        departure_datetime = datetime.now(tz)
        arrival_datetime = departure_datetime + timedelta(hours=24)
        ticket = Ticket.create(
            user_id=Id(uuid7()),
            city_snapshot=sample_city_snapshot,
            airship_snapshot=sample_airship_snapshot,
            cost_points=300,
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            created_at=departure_datetime,
            updated_at=departure_datetime,
        )
        assert ticket.status == TicketStatus.PURCHASED

        # When
        ticket.consume()

        # Then
        assert ticket.status == TicketStatus.BOARDING

    def test_consume_ticket_from_non_purchased_status_raises_error(
        self, sample_city_snapshot: CitySnapshot, sample_airship_snapshot: AirshipSnapshot, tz: ZoneInfo
    ):
        """PURCHASED가 아닌 상태의 티켓을 소비하려 하면 에러가 발생한다"""
        # Given
        departure_datetime = datetime.now(tz)
        arrival_datetime = departure_datetime + timedelta(hours=24)
        ticket = Ticket(
            ticket_id=Id(uuid7()),
            user_id=Id(uuid7()),
            city_snapshot=sample_city_snapshot,
            airship_snapshot=sample_airship_snapshot,
            ticket_number="B0-2025-12345",
            cost_points=300,
            status=TicketStatus.BOARDING,  # 이미 BOARDING 상태
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            created_at=departure_datetime,
            updated_at=departure_datetime,
        )

        # When/Then
        with pytest.raises(InvalidTicketStatusError):
            ticket.consume()

    def test_complete_ticket_from_boarding_status(
        self, sample_city_snapshot: CitySnapshot, sample_airship_snapshot: AirshipSnapshot, tz: ZoneInfo
    ):
        """BOARDING 상태의 티켓을 완료하여 COMPLETED 상태로 변경할 수 있다"""
        # Given
        departure_datetime = datetime.now(tz)
        arrival_datetime = departure_datetime + timedelta(hours=24)
        ticket = Ticket(
            ticket_id=Id(uuid7()),
            user_id=Id(uuid7()),
            city_snapshot=sample_city_snapshot,
            airship_snapshot=sample_airship_snapshot,
            ticket_number="B0-2025-12345",
            cost_points=300,
            status=TicketStatus.BOARDING,
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            created_at=departure_datetime,
            updated_at=departure_datetime,
        )

        # When
        ticket.complete()

        # Then
        assert ticket.status == TicketStatus.COMPLETED

    def test_complete_ticket_from_non_boarding_status_raises_error(
        self, sample_city_snapshot: CitySnapshot, sample_airship_snapshot: AirshipSnapshot, tz: ZoneInfo
    ):
        """BOARDING이 아닌 상태의 티켓을 완료하려 하면 에러가 발생한다"""
        # Given
        departure_datetime = datetime.now(tz)
        arrival_datetime = departure_datetime + timedelta(hours=24)
        ticket = Ticket.create(
            user_id=Id(uuid7()),
            city_snapshot=sample_city_snapshot,
            airship_snapshot=sample_airship_snapshot,
            cost_points=300,
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            created_at=departure_datetime,
            updated_at=departure_datetime,
        )
        assert ticket.status == TicketStatus.PURCHASED

        # When/Then
        with pytest.raises(InvalidTicketStatusError):
            ticket.complete()

    def test_cancel_ticket_from_purchased_status(
        self, sample_city_snapshot: CitySnapshot, sample_airship_snapshot: AirshipSnapshot, tz: ZoneInfo
    ):
        """PURCHASED 상태의 티켓을 취소하여 CANCELLED 상태로 변경할 수 있다"""
        # Given
        departure_datetime = datetime.now(tz)
        arrival_datetime = departure_datetime + timedelta(hours=24)
        ticket = Ticket.create(
            user_id=Id(uuid7()),
            city_snapshot=sample_city_snapshot,
            airship_snapshot=sample_airship_snapshot,
            cost_points=300,
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            created_at=departure_datetime,
            updated_at=departure_datetime,
        )
        assert ticket.status == TicketStatus.PURCHASED

        # When
        ticket.cancel()

        # Then
        assert ticket.status == TicketStatus.CANCELLED

    def test_cancel_ticket_from_non_purchased_status_raises_error(
        self, sample_city_snapshot: CitySnapshot, sample_airship_snapshot: AirshipSnapshot, tz: ZoneInfo
    ):
        """PURCHASED가 아닌 상태의 티켓을 취소하려 하면 에러가 발생한다"""
        # Given
        departure_datetime = datetime.now(tz)
        arrival_datetime = departure_datetime + timedelta(hours=24)
        ticket = Ticket(
            ticket_id=Id(uuid7()),
            user_id=Id(uuid7()),
            city_snapshot=sample_city_snapshot,
            airship_snapshot=sample_airship_snapshot,
            ticket_number="B0-2025-12345",
            cost_points=300,
            status=TicketStatus.BOARDING,
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            created_at=departure_datetime,
            updated_at=departure_datetime,
        )

        # When/Then
        with pytest.raises(InvalidTicketStatusError):
            ticket.cancel()

    def test_cancel_completed_ticket_raises_error(
        self, sample_city_snapshot: CitySnapshot, sample_airship_snapshot: AirshipSnapshot, tz: ZoneInfo
    ):
        """COMPLETED 상태의 티켓은 취소할 수 없다"""
        # Given
        departure_datetime = datetime.now(tz)
        arrival_datetime = departure_datetime + timedelta(hours=24)
        ticket = Ticket(
            ticket_id=Id(uuid7()),
            user_id=Id(uuid7()),
            city_snapshot=sample_city_snapshot,
            airship_snapshot=sample_airship_snapshot,
            ticket_number="B0-2025-12345",
            cost_points=300,
            status=TicketStatus.COMPLETED,
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            created_at=departure_datetime,
            updated_at=departure_datetime,
        )

        # When/Then
        with pytest.raises(InvalidTicketStatusError):
            ticket.cancel()

    def test_create_ticket_with_different_cost_and_duration(
        self, sample_city_snapshot: CitySnapshot, sample_airship_snapshot: AirshipSnapshot, tz: ZoneInfo
    ):
        """다양한 비용과 기간으로 티켓을 생성할 수 있다"""
        # Given
        user_id = Id(uuid7())
        cost_points = 500
        departure_datetime = datetime.now(tz)
        arrival_datetime = departure_datetime + timedelta(hours=12)

        # When
        ticket = Ticket.create(
            user_id=user_id,
            city_snapshot=sample_city_snapshot,
            airship_snapshot=sample_airship_snapshot,
            cost_points=cost_points,
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            created_at=departure_datetime,
            updated_at=departure_datetime,
        )

        # Then
        assert ticket.cost_points == 500
        assert ticket.arrival_datetime == departure_datetime + timedelta(hours=12)
