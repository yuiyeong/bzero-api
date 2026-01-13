from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.orm import Session
from uuid_utils import uuid7

from bzero.domain.entities import Airship, City, Ticket
from bzero.domain.errors import NotFoundTicketError
from bzero.domain.services.ticket import TicketSyncService
from bzero.domain.value_objects import Id, TicketStatus
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.ticket import SqlAlchemyTicketSyncRepository


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone"""
    return ZoneInfo("Asia/Seoul")


@pytest.fixture
def ticket_sync_service(test_sync_session: Session) -> TicketSyncService:
    """TicketSyncService fixture를 생성합니다."""
    ticket_repository = SqlAlchemyTicketSyncRepository(test_sync_session)
    return TicketSyncService(ticket_repository)


@pytest.fixture
def sync_sample_user(test_sync_session: Session) -> UserModel:
    """테스트용 샘플 유저 데이터를 생성합니다."""
    now = datetime.now()
    user_model = UserModel(
        user_id=uuid7(),
        email="test@example.com",
        nickname="테스트유저",
        profile_emoji="🌟",
        current_points=1000,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(user_model)
    test_sync_session.flush()
    return user_model


@pytest.fixture
def sync_sample_city(test_sync_session: Session) -> CityModel:
    """테스트용 샘플 도시 데이터를 생성합니다."""
    now = datetime.now()
    city_model = CityModel(
        city_id=uuid7(),
        name="세렌시아",
        theme="관계",
        image_url="https://example.com/serencia.jpg",
        description="노을빛 항구 마을",
        base_cost_points=300,
        base_duration_minutes=24,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(city_model)
    test_sync_session.flush()
    return city_model


@pytest.fixture
def sync_sample_airship(test_sync_session: Session) -> AirshipModel:
    """테스트용 샘플 비행선 데이터를 생성합니다."""
    now = datetime.now()
    airship_model = AirshipModel(
        airship_id=uuid7(),
        name="일반 비행선",
        description="편안하고 여유로운 여행을 원하는 여행자를 위한 비행선",
        image_url="https://example.com/normal.jpg",
        cost_factor=1,
        duration_factor=1,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(airship_model)
    test_sync_session.flush()
    return airship_model


def _create_city_entity(city_model: CityModel) -> City:
    """CityModel을 City 엔티티로 변환합니다."""
    return City(
        city_id=Id(city_model.city_id),
        name=city_model.name,
        theme=city_model.theme,
        image_url=city_model.image_url,
        description=city_model.description,
        base_cost_points=city_model.base_cost_points,
        base_duration_minutes=city_model.base_duration_minutes,
        display_order=city_model.display_order,
        is_active=city_model.is_active,
        created_at=city_model.created_at,
        updated_at=city_model.updated_at,
    )


def _create_airship_entity(airship_model: AirshipModel) -> Airship:
    """AirshipModel을 Airship 엔티티로 변환합니다."""
    return Airship(
        airship_id=Id(airship_model.airship_id),
        name=airship_model.name,
        description=airship_model.description,
        image_url=airship_model.image_url,
        cost_factor=airship_model.cost_factor,
        duration_factor=airship_model.duration_factor,
        display_order=airship_model.display_order,
        is_active=airship_model.is_active,
        created_at=airship_model.created_at,
        updated_at=airship_model.updated_at,
    )


@pytest.fixture
def sync_sample_ticket(
    test_sync_session: Session,
    sync_sample_user: UserModel,
    sync_sample_city: CityModel,
    sync_sample_airship: AirshipModel,
    timezone: ZoneInfo,
) -> Ticket:
    """테스트용 샘플 BOARDING 상태 티켓 데이터를 생성합니다."""
    now = datetime.now(timezone)
    city = _create_city_entity(sync_sample_city)
    airship = _create_airship_entity(sync_sample_airship)

    ticket = Ticket.create(
        user_id=Id(sync_sample_user.user_id),
        city_snapshot=city.snapshot(),
        airship_snapshot=airship.snapshot(),
        cost_points=300,
        departure_datetime=now,
        arrival_datetime=now + timedelta(hours=24),
        created_at=now,
        updated_at=now,
    )
    # BOARDING 상태로 변경
    ticket.consume()

    ticket_model = TicketModel(
        ticket_id=ticket.ticket_id.value,
        user_id=ticket.user_id.value,
        ticket_number=ticket.ticket_number,
        cost_points=ticket.cost_points,
        status=ticket.status.value,
        departure_datetime=ticket.departure_datetime,
        arrival_datetime=ticket.arrival_datetime,
        city_id=ticket.city_snapshot.city_id.value,
        city_name=ticket.city_snapshot.name,
        city_theme=ticket.city_snapshot.theme,
        city_image_url=ticket.city_snapshot.image_url,
        city_description=ticket.city_snapshot.description,
        city_base_cost_points=ticket.city_snapshot.base_cost_points,
        city_base_duration_minutes=ticket.city_snapshot.base_duration_minutes,
        airship_id=ticket.airship_snapshot.airship_id.value,
        airship_name=ticket.airship_snapshot.name,
        airship_image_url=ticket.airship_snapshot.image_url,
        airship_description=ticket.airship_snapshot.description,
        airship_cost_factor=ticket.airship_snapshot.cost_factor,
        airship_duration_factor=ticket.airship_snapshot.duration_factor,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )
    test_sync_session.add(ticket_model)
    test_sync_session.flush()

    return ticket


class TestTicketSyncServiceGetTicketById:
    """get_ticket_by_id 메서드 통합 테스트"""

    def test_get_ticket_by_id_success(
        self,
        ticket_sync_service: TicketSyncService,
        sync_sample_ticket: Ticket,
    ):
        """티켓을 ID로 조회할 수 있어야 합니다."""
        # When
        ticket = ticket_sync_service.get_ticket_by_id(sync_sample_ticket.ticket_id)

        # Then
        assert str(ticket.ticket_id.value) == str(sync_sample_ticket.ticket_id.value)
        assert str(ticket.user_id.value) == str(sync_sample_ticket.user_id.value)
        assert ticket.status == TicketStatus.BOARDING

    def test_get_ticket_by_id_raises_error_when_not_found(
        self,
        ticket_sync_service: TicketSyncService,
    ):
        """티켓을 찾을 수 없으면 에러가 발생해야 합니다."""
        # Given
        non_existent_ticket_id = Id(str(uuid7()))

        # When/Then
        with pytest.raises(NotFoundTicketError):
            ticket_sync_service.get_ticket_by_id(non_existent_ticket_id)


class TestTicketSyncServiceComplete:
    """complete 메서드 통합 테스트"""

    def test_complete_ticket_success(
        self,
        ticket_sync_service: TicketSyncService,
        sync_sample_ticket: Ticket,
        test_sync_session: Session,
    ):
        """BOARDING 상태 티켓을 COMPLETED로 변경할 수 있어야 합니다."""
        # Given: BOARDING 상태의 티켓
        assert sync_sample_ticket.status == TicketStatus.BOARDING

        # When
        completed_ticket = ticket_sync_service.complete(sync_sample_ticket.ticket_id)

        # Then
        assert completed_ticket.status == TicketStatus.COMPLETED
        assert str(completed_ticket.ticket_id.value) == str(sync_sample_ticket.ticket_id.value)

    def test_complete_raises_error_when_ticket_not_found(
        self,
        ticket_sync_service: TicketSyncService,
    ):
        """티켓을 찾을 수 없으면 에러가 발생해야 합니다."""
        # Given
        non_existent_ticket_id = Id(str(uuid7()))

        # When/Then
        with pytest.raises(NotFoundTicketError):
            ticket_sync_service.complete(non_existent_ticket_id)
