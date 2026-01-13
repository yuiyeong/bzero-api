from collections.abc import Iterator
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
from bzero.infrastructure.db.room_model import RoomModel
from bzero.infrastructure.db.room_stay_model import RoomStayModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.worker.tasks.room_stays.task_check_in import task_check_in


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
    ticket_id: str | None = None,
) -> TicketModel:
    """테스트용 티켓 모델을 생성합니다."""
    now = datetime.now(timezone)
    _ticket_id = ticket_id or str(uuid7())

    ticket_model = TicketModel(
        ticket_id=_ticket_id,
        user_id=user_id,
        ticket_number=f"B0-{now.year}-test123",
        cost_points=300,
        status=status.value,
        departure_datetime=now - timedelta(hours=24),  # 24시간 전 출발
        arrival_datetime=now,  # 지금 도착
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


class TestCheckInTask:
    """task_check_in 태스크 통합 테스트"""

    def test_check_in_success(
        self,
        test_sync_session: Session,
        sample_test_data: dict,
        timezone: ZoneInfo,
    ):
        """COMPLETED 상태의 티켓으로 체크인에 성공해야 합니다."""
        # Given: COMPLETED 상태의 티켓 생성
        ticket_model = create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.COMPLETED,
            timezone=timezone,
        )
        ticket_id_hex = ticket_model.ticket_id

        @contextmanager
        def mock_get_sync_db_session() -> Iterator[Session]:
            yield test_sync_session

        with patch(
            "bzero.worker.tasks.room_stays.task_check_in.get_sync_db_session",
            mock_get_sync_db_session,
        ):
            # When: 태스크 직접 호출
            result = task_check_in(ticket_id_hex)

        # Then: 성공 결과 확인
        assert result["ticket_id"] == ticket_id_hex
        assert result["result"] == "success"
        assert "room_stay_id" in result

        # DB에서 RoomStay 확인
        stmt = select(RoomStayModel).where(RoomStayModel.ticket_id == ticket_id_hex)
        db_result = test_sync_session.execute(stmt)
        room_stay = db_result.scalar_one()
        assert room_stay is not None
        assert room_stay.status == RoomStayStatus.CHECKED_IN.value
        assert str(room_stay.user_id) == sample_test_data["user_id"]
        assert str(room_stay.city_id) == sample_test_data["city_id"]
        assert str(room_stay.guest_house_id) == sample_test_data["guest_house_id"]

        # Room의 current_capacity 증가 확인
        stmt = select(RoomModel).where(RoomModel.room_id == room_stay.room_id)
        db_result = test_sync_session.execute(stmt)
        room = db_result.scalar_one()
        assert room.current_capacity == 1

    def test_check_in_ticket_not_found(
        self,
        test_sync_session: Session,
    ):
        """존재하지 않는 티켓 ID로 호출하면 실패해야 합니다."""
        # Given: 존재하지 않는 티켓 ID
        non_existent_ticket_id = str(uuid7())

        @contextmanager
        def mock_get_sync_db_session() -> Iterator[Session]:
            yield test_sync_session

        with patch(
            "bzero.worker.tasks.room_stays.task_check_in.get_sync_db_session",
            mock_get_sync_db_session,
        ):
            # When: 태스크 직접 호출
            result = task_check_in(non_existent_ticket_id)

        # Then: 실패 결과 확인
        assert result["ticket_id"] == non_existent_ticket_id
        assert "failed" in result["result"]
        assert "티켓" in result["result"]  # NotFoundTicketError 메시지 확인

    def test_check_in_invalid_status_boarding(
        self,
        test_sync_session: Session,
        sample_test_data: dict,
        timezone: ZoneInfo,
    ):
        """BOARDING 상태의 티켓은 체크인할 수 없어야 합니다."""
        # Given: BOARDING 상태의 티켓 생성
        ticket_model = create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.BOARDING,
            timezone=timezone,
        )
        ticket_id_hex = ticket_model.ticket_id

        @contextmanager
        def mock_get_sync_db_session() -> Iterator[Session]:
            yield test_sync_session

        with patch(
            "bzero.worker.tasks.room_stays.task_check_in.get_sync_db_session",
            mock_get_sync_db_session,
        ):
            # When: 태스크 직접 호출
            result = task_check_in(ticket_id_hex)

        # Then: 실패 결과 확인
        assert result["ticket_id"] == ticket_id_hex
        assert "failed" in result["result"]
        assert "티켓 상태" in result["result"]  # InvalidTicketStatusError 메시지 확인

    def test_check_in_invalid_status_purchased(
        self,
        test_sync_session: Session,
        sample_test_data: dict,
        timezone: ZoneInfo,
    ):
        """PURCHASED 상태의 티켓은 체크인할 수 없어야 합니다."""
        # Given: PURCHASED 상태의 티켓 생성
        ticket_model = create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.PURCHASED,
            timezone=timezone,
        )
        ticket_id_hex = ticket_model.ticket_id

        @contextmanager
        def mock_get_sync_db_session() -> Iterator[Session]:
            yield test_sync_session

        with patch(
            "bzero.worker.tasks.room_stays.task_check_in.get_sync_db_session",
            mock_get_sync_db_session,
        ):
            # When: 태스크 직접 호출
            result = task_check_in(ticket_id_hex)

        # Then: 실패 결과 확인
        assert result["ticket_id"] == ticket_id_hex
        assert "failed" in result["result"]
        assert "티켓 상태" in result["result"]  # InvalidTicketStatusError 메시지 확인

    def test_check_in_guest_house_not_found(
        self,
        test_sync_session: Session,
        timezone: ZoneInfo,
    ):
        """도시에 게스트하우스가 없으면 실패해야 합니다."""
        # Given: 게스트하우스 없이 User, City, Airship만 생성
        user = create_user_model(test_sync_session)
        city = create_city_model(test_sync_session)  # 게스트하우스 생성 안함
        airship = create_airship_model(test_sync_session)

        ticket_model = create_ticket_model(
            test_sync_session,
            user_id=str(user.user_id),
            city_id=str(city.city_id),
            airship_id=str(airship.airship_id),
            status=TicketStatus.COMPLETED,
            timezone=timezone,
        )
        ticket_id_hex = ticket_model.ticket_id

        @contextmanager
        def mock_get_sync_db_session() -> Iterator[Session]:
            yield test_sync_session

        with patch(
            "bzero.worker.tasks.room_stays.task_check_in.get_sync_db_session",
            mock_get_sync_db_session,
        ):
            # When: 태스크 직접 호출
            result = task_check_in(ticket_id_hex)

        # Then: 실패 결과 확인
        assert result["ticket_id"] == ticket_id_hex
        assert "failed" in result["result"]
        assert "게스트 하우스" in result["result"]  # NotFoundGuestHouseError 메시지 확인

    def test_check_in_creates_new_room_when_no_rooms_exist(
        self,
        test_sync_session: Session,
        sample_test_data: dict,
        timezone: ZoneInfo,
    ):
        """이용 가능한 방이 없으면 새 방을 생성해야 합니다."""
        # Given: COMPLETED 상태의 티켓 생성 (방은 없음)
        ticket_model = create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.COMPLETED,
            timezone=timezone,
        )
        ticket_id_hex = ticket_model.ticket_id

        # 방이 없는지 확인
        stmt = select(RoomModel).where(RoomModel.guest_house_id == sample_test_data["guest_house_id"])
        db_result = test_sync_session.execute(stmt)
        rooms_before = db_result.scalars().all()
        assert len(rooms_before) == 0

        @contextmanager
        def mock_get_sync_db_session() -> Iterator[Session]:
            yield test_sync_session

        with patch(
            "bzero.worker.tasks.room_stays.task_check_in.get_sync_db_session",
            mock_get_sync_db_session,
        ):
            # When: 태스크 직접 호출
            result = task_check_in(ticket_id_hex)

        # Then: 성공하고 새 방이 생성됨
        assert result["result"] == "success"

        stmt = select(RoomModel).where(RoomModel.guest_house_id == sample_test_data["guest_house_id"])
        db_result = test_sync_session.execute(stmt)
        rooms_after = db_result.scalars().all()
        assert len(rooms_after) == 1
        assert rooms_after[0].current_capacity == 1
        assert rooms_after[0].max_capacity == 6

    def test_check_in_uses_existing_available_room(
        self,
        test_sync_session: Session,
        sample_test_data: dict,
        timezone: ZoneInfo,
    ):
        """이용 가능한 방이 있으면 기존 방을 사용해야 합니다."""
        # Given: 이용 가능한 방 생성
        now = datetime.now()
        existing_room = RoomModel(
            room_id=str(uuid7()),
            guest_house_id=sample_test_data["guest_house_id"],
            max_capacity=6,
            current_capacity=3,  # 3명 체류 중
            created_at=now,
            updated_at=now,
        )
        test_sync_session.add(existing_room)
        test_sync_session.flush()

        ticket_model = create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.COMPLETED,
            timezone=timezone,
        )
        ticket_id_hex = ticket_model.ticket_id

        @contextmanager
        def mock_get_sync_db_session() -> Iterator[Session]:
            yield test_sync_session

        with patch(
            "bzero.worker.tasks.room_stays.task_check_in.get_sync_db_session",
            mock_get_sync_db_session,
        ):
            # When: 태스크 직접 호출
            result = task_check_in(ticket_id_hex)

        # Then: 성공하고 기존 방의 용량이 증가
        assert result["result"] == "success"

        # 기존 방의 current_capacity가 4로 증가했는지 확인
        test_sync_session.refresh(existing_room)
        assert existing_room.current_capacity == 4

        # 새로운 방이 생성되지 않았는지 확인
        stmt = select(RoomModel).where(RoomModel.guest_house_id == sample_test_data["guest_house_id"])
        db_result = test_sync_session.execute(stmt)
        rooms = db_result.scalars().all()
        assert len(rooms) == 1
