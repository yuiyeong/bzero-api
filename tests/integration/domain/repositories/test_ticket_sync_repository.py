"""TicketSyncRepository Integration Tests."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.orm import Session
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.value_objects import TicketStatus
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.ticket import SqlAlchemyTicketSyncRepository


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone"""
    return get_settings().timezone


@pytest.fixture
def ticket_sync_repository(test_sync_session: Session) -> SqlAlchemyTicketSyncRepository:
    """TicketSyncRepository fixture를 생성합니다."""
    return SqlAlchemyTicketSyncRepository(test_sync_session)


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


def create_ticket_model(
    session: Session,
    user_id: str,
    city_model: CityModel,
    airship_model: AirshipModel,
    status: TicketStatus,
    timezone: ZoneInfo,
    arrival_datetime: datetime | None = None,
) -> TicketModel:
    """테스트용 티켓 모델을 생성합니다."""
    now = datetime.now(timezone)
    _arrival_datetime = arrival_datetime or (now + timedelta(hours=24))

    ticket_model = TicketModel(
        ticket_id=str(uuid7()),
        user_id=user_id,
        ticket_number=f"B0-{now.year}-test{uuid7().hex[:6]}",
        cost_points=300,
        status=status.value,
        departure_datetime=now - timedelta(hours=1),
        arrival_datetime=_arrival_datetime,
        city_id=str(city_model.city_id),
        city_name=city_model.name,
        city_theme=city_model.theme,
        city_image_url=city_model.image_url,
        city_description=city_model.description,
        city_base_cost_points=city_model.base_cost_points,
        city_base_duration_minutes=city_model.base_duration_minutes,
        airship_id=str(airship_model.airship_id),
        airship_name=airship_model.name,
        airship_image_url=airship_model.image_url,
        airship_description=airship_model.description,
        airship_cost_factor=airship_model.cost_factor,
        airship_duration_factor=airship_model.duration_factor,
        created_at=now,
        updated_at=now,
    )
    session.add(ticket_model)
    session.flush()
    return ticket_model


class TestFindIdsDueForCompletion:
    """find_ids_due_for_completion 메서드 테스트"""

    def test_returns_boarding_tickets_with_past_arrival(
        self,
        ticket_sync_repository: SqlAlchemyTicketSyncRepository,
        test_sync_session: Session,
        sync_sample_user: UserModel,
        sync_sample_city: CityModel,
        sync_sample_airship: AirshipModel,
        timezone: ZoneInfo,
    ):
        """도착 시간이 지난 BOARDING 티켓 ID를 반환해야 합니다."""
        # Given: BOARDING 상태이고 arrival_datetime이 지난 티켓 2개 생성
        now = datetime.now(timezone)
        past_arrival = now - timedelta(hours=1)

        ticket1 = create_ticket_model(
            test_sync_session,
            user_id=str(sync_sample_user.user_id),
            city_model=sync_sample_city,
            airship_model=sync_sample_airship,
            status=TicketStatus.BOARDING,
            timezone=timezone,
            arrival_datetime=past_arrival,
        )
        ticket2 = create_ticket_model(
            test_sync_session,
            user_id=str(sync_sample_user.user_id),
            city_model=sync_sample_city,
            airship_model=sync_sample_airship,
            status=TicketStatus.BOARDING,
            timezone=timezone,
            arrival_datetime=past_arrival - timedelta(hours=1),
        )

        # When
        ids = ticket_sync_repository.find_ids_due_for_completion(limit=100)

        # Then
        assert len(ids) == 2
        id_values = [str(id_.value) for id_ in ids]
        assert ticket1.ticket_id in id_values
        assert ticket2.ticket_id in id_values

    def test_excludes_boarding_tickets_with_future_arrival(
        self,
        ticket_sync_repository: SqlAlchemyTicketSyncRepository,
        test_sync_session: Session,
        sync_sample_user: UserModel,
        sync_sample_city: CityModel,
        sync_sample_airship: AirshipModel,
        timezone: ZoneInfo,
    ):
        """도착 시간이 지나지 않은 BOARDING 티켓은 제외해야 합니다."""
        # Given: arrival_datetime이 미래인 BOARDING 티켓
        now = datetime.now(timezone)
        future_arrival = now + timedelta(hours=1)

        create_ticket_model(
            test_sync_session,
            user_id=str(sync_sample_user.user_id),
            city_model=sync_sample_city,
            airship_model=sync_sample_airship,
            status=TicketStatus.BOARDING,
            timezone=timezone,
            arrival_datetime=future_arrival,
        )

        # When
        ids = ticket_sync_repository.find_ids_due_for_completion(limit=100)

        # Then
        assert len(ids) == 0

    def test_excludes_completed_tickets(
        self,
        ticket_sync_repository: SqlAlchemyTicketSyncRepository,
        test_sync_session: Session,
        sync_sample_user: UserModel,
        sync_sample_city: CityModel,
        sync_sample_airship: AirshipModel,
        timezone: ZoneInfo,
    ):
        """COMPLETED 상태 티켓은 제외해야 합니다."""
        # Given: arrival_datetime이 지났지만 COMPLETED 상태인 티켓
        now = datetime.now(timezone)
        past_arrival = now - timedelta(hours=1)

        create_ticket_model(
            test_sync_session,
            user_id=str(sync_sample_user.user_id),
            city_model=sync_sample_city,
            airship_model=sync_sample_airship,
            status=TicketStatus.COMPLETED,
            timezone=timezone,
            arrival_datetime=past_arrival,
        )

        # When
        ids = ticket_sync_repository.find_ids_due_for_completion(limit=100)

        # Then
        assert len(ids) == 0

    def test_excludes_cancelled_tickets(
        self,
        ticket_sync_repository: SqlAlchemyTicketSyncRepository,
        test_sync_session: Session,
        sync_sample_user: UserModel,
        sync_sample_city: CityModel,
        sync_sample_airship: AirshipModel,
        timezone: ZoneInfo,
    ):
        """CANCELLED 상태 티켓은 제외해야 합니다."""
        # Given: arrival_datetime이 지났지만 CANCELLED 상태인 티켓
        now = datetime.now(timezone)
        past_arrival = now - timedelta(hours=1)

        create_ticket_model(
            test_sync_session,
            user_id=str(sync_sample_user.user_id),
            city_model=sync_sample_city,
            airship_model=sync_sample_airship,
            status=TicketStatus.CANCELLED,
            timezone=timezone,
            arrival_datetime=past_arrival,
        )

        # When
        ids = ticket_sync_repository.find_ids_due_for_completion(limit=100)

        # Then
        assert len(ids) == 0

    def test_excludes_purchased_tickets(
        self,
        ticket_sync_repository: SqlAlchemyTicketSyncRepository,
        test_sync_session: Session,
        sync_sample_user: UserModel,
        sync_sample_city: CityModel,
        sync_sample_airship: AirshipModel,
        timezone: ZoneInfo,
    ):
        """PURCHASED 상태 티켓은 제외해야 합니다."""
        # Given: arrival_datetime이 지났지만 PURCHASED 상태인 티켓
        now = datetime.now(timezone)
        past_arrival = now - timedelta(hours=1)

        create_ticket_model(
            test_sync_session,
            user_id=str(sync_sample_user.user_id),
            city_model=sync_sample_city,
            airship_model=sync_sample_airship,
            status=TicketStatus.PURCHASED,
            timezone=timezone,
            arrival_datetime=past_arrival,
        )

        # When
        ids = ticket_sync_repository.find_ids_due_for_completion(limit=100)

        # Then
        assert len(ids) == 0

    def test_excludes_soft_deleted_tickets(
        self,
        ticket_sync_repository: SqlAlchemyTicketSyncRepository,
        test_sync_session: Session,
        sync_sample_user: UserModel,
        sync_sample_city: CityModel,
        sync_sample_airship: AirshipModel,
        timezone: ZoneInfo,
    ):
        """Soft delete된 티켓은 제외해야 합니다."""
        # Given: BOARDING 상태이고 arrival_datetime이 지났지만 soft deleted인 티켓
        now = datetime.now(timezone)
        past_arrival = now - timedelta(hours=1)

        ticket = create_ticket_model(
            test_sync_session,
            user_id=str(sync_sample_user.user_id),
            city_model=sync_sample_city,
            airship_model=sync_sample_airship,
            status=TicketStatus.BOARDING,
            timezone=timezone,
            arrival_datetime=past_arrival,
        )
        ticket.deleted_at = now
        test_sync_session.flush()

        # When
        ids = ticket_sync_repository.find_ids_due_for_completion(limit=100)

        # Then
        assert len(ids) == 0

    def test_respects_limit_parameter(
        self,
        ticket_sync_repository: SqlAlchemyTicketSyncRepository,
        test_sync_session: Session,
        sync_sample_user: UserModel,
        sync_sample_city: CityModel,
        sync_sample_airship: AirshipModel,
        timezone: ZoneInfo,
    ):
        """limit 파라미터를 준수해야 합니다."""
        # Given: 5개의 BOARDING 티켓 생성
        now = datetime.now(timezone)
        past_arrival = now - timedelta(hours=1)

        for _ in range(5):
            create_ticket_model(
                test_sync_session,
                user_id=str(sync_sample_user.user_id),
                city_model=sync_sample_city,
                airship_model=sync_sample_airship,
                status=TicketStatus.BOARDING,
                timezone=timezone,
                arrival_datetime=past_arrival,
            )

        # When: limit=3
        ids = ticket_sync_repository.find_ids_due_for_completion(limit=3)

        # Then
        assert len(ids) == 3

    def test_returns_empty_list_when_no_matching_tickets(
        self,
        ticket_sync_repository: SqlAlchemyTicketSyncRepository,
    ):
        """조건에 맞는 티켓이 없으면 빈 리스트를 반환해야 합니다."""
        # When
        ids = ticket_sync_repository.find_ids_due_for_completion(limit=100)

        # Then
        assert ids == []

    def test_mixed_tickets_only_returns_matching_ones(
        self,
        ticket_sync_repository: SqlAlchemyTicketSyncRepository,
        test_sync_session: Session,
        sync_sample_user: UserModel,
        sync_sample_city: CityModel,
        sync_sample_airship: AirshipModel,
        timezone: ZoneInfo,
    ):
        """다양한 상태의 티켓 중 조건에 맞는 것만 반환해야 합니다."""
        now = datetime.now(timezone)
        past_arrival = now - timedelta(hours=1)
        future_arrival = now + timedelta(hours=1)

        # BOARDING + 과거 arrival (조건 충족)
        matching_ticket = create_ticket_model(
            test_sync_session,
            user_id=str(sync_sample_user.user_id),
            city_model=sync_sample_city,
            airship_model=sync_sample_airship,
            status=TicketStatus.BOARDING,
            timezone=timezone,
            arrival_datetime=past_arrival,
        )

        # BOARDING + 미래 arrival (미충족)
        create_ticket_model(
            test_sync_session,
            user_id=str(sync_sample_user.user_id),
            city_model=sync_sample_city,
            airship_model=sync_sample_airship,
            status=TicketStatus.BOARDING,
            timezone=timezone,
            arrival_datetime=future_arrival,
        )

        # COMPLETED + 과거 arrival (미충족)
        create_ticket_model(
            test_sync_session,
            user_id=str(sync_sample_user.user_id),
            city_model=sync_sample_city,
            airship_model=sync_sample_airship,
            status=TicketStatus.COMPLETED,
            timezone=timezone,
            arrival_datetime=past_arrival,
        )

        # PURCHASED + 과거 arrival (미충족)
        create_ticket_model(
            test_sync_session,
            user_id=str(sync_sample_user.user_id),
            city_model=sync_sample_city,
            airship_model=sync_sample_airship,
            status=TicketStatus.PURCHASED,
            timezone=timezone,
            arrival_datetime=past_arrival,
        )

        # When
        ids = ticket_sync_repository.find_ids_due_for_completion(limit=100)

        # Then
        assert len(ids) == 1
        assert str(ids[0].value) == matching_ticket.ticket_id
