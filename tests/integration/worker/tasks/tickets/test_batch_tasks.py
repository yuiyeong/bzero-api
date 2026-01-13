"""티켓 배치 태스크 통합 테스트."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.value_objects import TicketStatus
from bzero.domain.value_objects.guesthouse import GuestHouseType
from bzero.domain.value_objects.room_stay import RoomStayStatus
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.room_stay_model import RoomStayModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.worker.tasks.tickets.batch import task_complete_tickets_and_check_in_batch


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone"""
    return get_settings().timezone


def create_user_model(session: Session) -> UserModel:
    """테스트용 사용자 모델을 생성합니다."""
    now = datetime.now()
    user_model = UserModel(
        user_id=str(uuid7()),
        email="test@example.com",
        nickname="테스트유저",
        profile_emoji="🌟",
        current_points=1000,
        created_at=now,
        updated_at=now,
    )
    session.add(user_model)
    session.flush()
    return user_model


def create_city_model(session: Session) -> CityModel:
    """테스트용 도시 모델을 생성합니다."""
    now = datetime.now()
    city_model = CityModel(
        city_id=str(uuid7()),
        name="세렌시아",
        theme="관계",
        image_url="https://example.com/city.jpg",
        description="노을빛 항구 마을",
        base_cost_points=300,
        base_duration_minutes=24,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(city_model)
    session.flush()
    return city_model


def create_airship_model(session: Session) -> AirshipModel:
    """테스트용 비행선 모델을 생성합니다."""
    now = datetime.now()
    airship_model = AirshipModel(
        airship_id=str(uuid7()),
        name="일반 비행선",
        description="편안한 여행",
        image_url="https://example.com/airship.jpg",
        cost_factor=1,
        duration_factor=1,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(airship_model)
    session.flush()
    return airship_model


def create_guest_house_model(session: Session, city_id: str) -> GuestHouseModel:
    """테스트용 게스트하우스 모델을 생성합니다."""
    now = datetime.now()
    guest_house_model = GuestHouseModel(
        guest_house_id=str(uuid7()),
        city_id=city_id,
        guest_house_type=GuestHouseType.MIXED.value,
        name="세렌시아 게스트하우스",
        description="노을빛 항구 마을의 게스트하우스",
        image_url="https://example.com/guesthouse.jpg",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(guest_house_model)
    session.flush()
    return guest_house_model


def create_ticket_model(
    session: Session,
    user_id: str,
    city_id: str,
    airship_id: str,
    status: TicketStatus,
    timezone: ZoneInfo,
    arrival_datetime: datetime | None = None,
) -> TicketModel:
    """테스트용 티켓 모델을 생성합니다."""
    now = datetime.now(timezone)
    _arrival_datetime = arrival_datetime or now

    ticket_model = TicketModel(
        ticket_id=str(uuid7()),
        user_id=user_id,
        ticket_number=f"B0-{now.year}-test{uuid7().hex[:6]}",
        cost_points=300,
        status=status.value,
        departure_datetime=now - timedelta(hours=24),
        arrival_datetime=_arrival_datetime,
        city_id=city_id,
        city_name="세렌시아",
        city_theme="관계",
        city_image_url="https://example.com/city.jpg",
        city_description="노을빛 항구 마을",
        city_base_cost_points=300,
        city_base_duration_minutes=24,
        airship_id=airship_id,
        airship_name="일반 비행선",
        airship_image_url="https://example.com/airship.jpg",
        airship_description="편안한 여행",
        airship_cost_factor=1.0,
        airship_duration_factor=1.0,
        created_at=now,
        updated_at=now,
    )

    session.add(ticket_model)
    session.flush()

    return ticket_model


@pytest.fixture
def sample_test_data(test_sync_session: Session) -> dict:
    """테스트에 필요한 기본 데이터(User, City, Airship, GuestHouse)를 생성합니다."""
    user = create_user_model(test_sync_session)
    city = create_city_model(test_sync_session)
    airship = create_airship_model(test_sync_session)
    guest_house = create_guest_house_model(test_sync_session, str(city.city_id))

    return {
        "user_id": str(user.user_id),
        "city_id": str(city.city_id),
        "airship_id": str(airship.airship_id),
        "guest_house_id": str(guest_house.guest_house_id),
    }


@pytest.fixture
def mock_session_factory(test_sync_session: Session) -> Callable[[], Iterator[Session]]:
    """테스트용 세션 팩토리를 반환합니다."""

    @contextmanager
    def mock_factory() -> Iterator[Session]:
        yield test_sync_session

    return mock_factory


class TestCompleteTicketsAndCheckInBatchTask:
    """task_complete_tickets_and_check_in_batch 태스크 통합 테스트"""

    def test_batch_processes_boarding_tickets_with_past_arrival(
        self,
        test_sync_session: Session,
        sample_test_data: dict,
        timezone: ZoneInfo,
        mock_session_factory: Callable[[], Iterator[Session]],
    ):
        """도착 시간이 지난 BOARDING 티켓을 완료 처리하고 체크인해야 합니다."""
        # Given: BOARDING 상태이고 arrival_datetime이 지난 티켓 2개 생성
        now = datetime.now(timezone)
        past_arrival = now - timedelta(hours=1)

        ticket1 = create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.BOARDING,
            timezone=timezone,
            arrival_datetime=past_arrival,
        )
        ticket2 = create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.BOARDING,
            timezone=timezone,
            arrival_datetime=past_arrival - timedelta(minutes=30),
        )

        with patch(
            "bzero.worker.tasks.tickets.batch.get_sync_session_factory",
            return_value=mock_session_factory,
        ):
            # When: 배치 태스크 실행
            result = task_complete_tickets_and_check_in_batch()

        # Then: 결과 확인
        assert result["total"] == 2
        assert result["processed"] == 2
        assert result["failed"] == 0

        # DB에서 티켓 상태 확인
        stmt = select(TicketModel).where(TicketModel.ticket_id == ticket1.ticket_id)
        db_ticket1 = test_sync_session.execute(stmt).scalar_one()
        assert db_ticket1.status == TicketStatus.COMPLETED.value

        stmt = select(TicketModel).where(TicketModel.ticket_id == ticket2.ticket_id)
        db_ticket2 = test_sync_session.execute(stmt).scalar_one()
        assert db_ticket2.status == TicketStatus.COMPLETED.value

        # RoomStay 생성 확인
        stmt = select(RoomStayModel).where(RoomStayModel.ticket_id == ticket1.ticket_id)
        room_stay1 = test_sync_session.execute(stmt).scalar_one()
        assert room_stay1.status == RoomStayStatus.CHECKED_IN.value

        stmt = select(RoomStayModel).where(RoomStayModel.ticket_id == ticket2.ticket_id)
        room_stay2 = test_sync_session.execute(stmt).scalar_one()
        assert room_stay2.status == RoomStayStatus.CHECKED_IN.value

    def test_batch_returns_zero_when_no_tickets_to_process(
        self,
        test_sync_session: Session,
        mock_session_factory: Callable[[], Iterator[Session]],
    ):
        """처리할 티켓이 없으면 0을 반환해야 합니다."""
        with patch(
            "bzero.worker.tasks.tickets.batch.get_sync_session_factory",
            return_value=mock_session_factory,
        ):
            # When: 배치 태스크 실행
            result = task_complete_tickets_and_check_in_batch()

        # Then
        assert result["total"] == 0
        assert result["processed"] == 0
        assert result["failed"] == 0

    def test_batch_skips_boarding_tickets_with_future_arrival(
        self,
        test_sync_session: Session,
        sample_test_data: dict,
        timezone: ZoneInfo,
        mock_session_factory: Callable[[], Iterator[Session]],
    ):
        """도착 시간이 지나지 않은 BOARDING 티켓은 처리하지 않아야 합니다."""
        # Given: arrival_datetime이 미래인 BOARDING 티켓
        now = datetime.now(timezone)
        future_arrival = now + timedelta(hours=1)

        create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.BOARDING,
            timezone=timezone,
            arrival_datetime=future_arrival,
        )

        with patch(
            "bzero.worker.tasks.tickets.batch.get_sync_session_factory",
            return_value=mock_session_factory,
        ):
            # When: 배치 태스크 실행
            result = task_complete_tickets_and_check_in_batch()

        # Then
        assert result["total"] == 0
        assert result["processed"] == 0

    def test_batch_skips_completed_tickets(
        self,
        test_sync_session: Session,
        sample_test_data: dict,
        timezone: ZoneInfo,
        mock_session_factory: Callable[[], Iterator[Session]],
    ):
        """COMPLETED 상태 티켓은 처리하지 않아야 합니다."""
        # Given: arrival_datetime이 지났지만 COMPLETED 상태인 티켓
        now = datetime.now(timezone)
        past_arrival = now - timedelta(hours=1)

        create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.COMPLETED,
            timezone=timezone,
            arrival_datetime=past_arrival,
        )

        with patch(
            "bzero.worker.tasks.tickets.batch.get_sync_session_factory",
            return_value=mock_session_factory,
        ):
            # When: 배치 태스크 실행
            result = task_complete_tickets_and_check_in_batch()

        # Then
        assert result["total"] == 0
        assert result["processed"] == 0

    def test_batch_skips_cancelled_tickets(
        self,
        test_sync_session: Session,
        sample_test_data: dict,
        timezone: ZoneInfo,
        mock_session_factory: Callable[[], Iterator[Session]],
    ):
        """CANCELLED 상태 티켓은 처리하지 않아야 합니다."""
        # Given: arrival_datetime이 지났지만 CANCELLED 상태인 티켓
        now = datetime.now(timezone)
        past_arrival = now - timedelta(hours=1)

        create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.CANCELLED,
            timezone=timezone,
            arrival_datetime=past_arrival,
        )

        with patch(
            "bzero.worker.tasks.tickets.batch.get_sync_session_factory",
            return_value=mock_session_factory,
        ):
            # When: 배치 태스크 실행
            result = task_complete_tickets_and_check_in_batch()

        # Then
        assert result["total"] == 0
        assert result["processed"] == 0

    def test_batch_continues_processing_after_error(
        self,
        test_sync_session: Session,
        sample_test_data: dict,
        timezone: ZoneInfo,
        mock_session_factory: Callable[[], Iterator[Session]],
    ):
        """한 티켓 처리 실패 시에도 다른 티켓 처리를 계속해야 합니다."""
        # Given: 2개의 티켓 (하나는 게스트하우스 없는 도시)
        now = datetime.now(timezone)
        past_arrival = now - timedelta(hours=1)

        # 정상 티켓
        normal_ticket = create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.BOARDING,
            timezone=timezone,
            arrival_datetime=past_arrival,
        )

        # 게스트하우스 없는 도시에 대한 티켓 (에러 발생 예상)
        another_city = create_city_model(test_sync_session)  # 게스트하우스 없음
        error_ticket = create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=str(another_city.city_id),
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.BOARDING,
            timezone=timezone,
            arrival_datetime=past_arrival - timedelta(minutes=10),
        )

        with patch(
            "bzero.worker.tasks.tickets.batch.get_sync_session_factory",
            return_value=mock_session_factory,
        ):
            # When: 배치 태스크 실행
            result = task_complete_tickets_and_check_in_batch()

        # Then: 1개 성공, 1개 실패 (티켓 완료는 되지만 체크인 실패)
        assert result["total"] == 2
        assert result["processed"] == 1
        assert result["failed"] == 1

        # 정상 티켓은 완료 처리됨
        stmt = select(TicketModel).where(TicketModel.ticket_id == normal_ticket.ticket_id)
        db_normal_ticket = test_sync_session.execute(stmt).scalar_one()
        assert db_normal_ticket.status == TicketStatus.COMPLETED.value

        # 에러 티켓은 롤백되어 BOARDING 상태 유지
        stmt = select(TicketModel).where(TicketModel.ticket_id == error_ticket.ticket_id)
        db_error_ticket = test_sync_session.execute(stmt).scalar_one()
        assert db_error_ticket.status == TicketStatus.BOARDING.value

    def test_batch_mixed_tickets_only_processes_matching(
        self,
        test_sync_session: Session,
        sample_test_data: dict,
        timezone: ZoneInfo,
        mock_session_factory: Callable[[], Iterator[Session]],
    ):
        """다양한 상태의 티켓 중 조건에 맞는 것만 처리해야 합니다."""
        now = datetime.now(timezone)
        past_arrival = now - timedelta(hours=1)
        future_arrival = now + timedelta(hours=1)

        # BOARDING + 과거 arrival (처리 대상)
        matching_ticket = create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.BOARDING,
            timezone=timezone,
            arrival_datetime=past_arrival,
        )

        # BOARDING + 미래 arrival (처리 대상 아님)
        create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.BOARDING,
            timezone=timezone,
            arrival_datetime=future_arrival,
        )

        # COMPLETED + 과거 arrival (처리 대상 아님)
        create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.COMPLETED,
            timezone=timezone,
            arrival_datetime=past_arrival,
        )

        with patch(
            "bzero.worker.tasks.tickets.batch.get_sync_session_factory",
            return_value=mock_session_factory,
        ):
            # When: 배치 태스크 실행
            result = task_complete_tickets_and_check_in_batch()

        # Then
        assert result["total"] == 1
        assert result["processed"] == 1
        assert result["failed"] == 0

        # 조건에 맞는 티켓만 COMPLETED로 변경됨
        stmt = select(TicketModel).where(TicketModel.ticket_id == matching_ticket.ticket_id)
        db_ticket = test_sync_session.execute(stmt).scalar_one()
        assert db_ticket.status == TicketStatus.COMPLETED.value
