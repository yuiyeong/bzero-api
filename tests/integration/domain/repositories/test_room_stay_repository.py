from datetime import datetime, timedelta

import pytest

from bzero.domain.value_objects import Id, RoomStayStatus
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.room_model import RoomModel
from bzero.infrastructure.db.room_stay_model import RoomStayModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.room_stay import SqlAlchemyRoomStayRepository


@pytest.fixture
async def setup_dependencies(test_session):
    # 0. Airship
    airship_id = Id().value
    airship = AirshipModel(
        airship_id=airship_id,
        name="Test Airship",
        description="Test Desc",
        image_url="url",
        cost_factor=1,
        duration_factor=1,
        display_order=1,
        is_active=True,
    )
    test_session.add(airship)

    # 1. User
    user_id = Id().value
    user = UserModel(user_id=user_id, email="test@example.com")
    test_session.add(user)

    # 2. City
    city_id = Id().value
    city = CityModel(
        city_id=city_id,
        name="Test City",
        theme="Modern",
        description="Desc",
        image_url="url",
        base_cost_points=100,
        base_duration_minutes=2,
        is_active=True,
        display_order=1,
    )
    test_session.add(city)

    # 3. GuestHouse
    gh_id = Id().value
    gh = GuestHouseModel(
        guest_house_id=gh_id,
        city_id=city_id,
        guest_house_type="MIXED",
        name="Test GH",
        description="Desc",
        image_url="url",
        is_active=True,
    )
    test_session.add(gh)

    # 4. Room
    room_id = Id().value
    room = RoomModel(room_id=room_id, guest_house_id=gh_id, max_capacity=4, current_capacity=0)
    test_session.add(room)
    await test_session.flush()

    # 5. Ticket
    ticket_id = Id().value
    ticket = TicketModel(
        ticket_id=ticket_id,
        user_id=user_id,
        city_id=city_id,
        city_name="Test City",
        city_theme="Modern",
        city_description="Desc",
        city_image_url="url",
        city_base_cost_points=100,
        city_base_duration_minutes=2,
        airship_id=airship_id,
        airship_name="Test Airship",
        airship_description="Test Desc",
        airship_image_url="url",
        airship_cost_factor=1,
        airship_duration_factor=1,
        ticket_number="T-123",
        cost_points=100,
        status="completed",
        departure_datetime=datetime.now(),
        arrival_datetime=datetime.now(),
    )
    test_session.add(ticket)

    await test_session.flush()
    return {"user_id": user_id, "city_id": city_id, "gh_id": gh_id, "room_id": room_id, "ticket_id": ticket_id}


@pytest.mark.asyncio
class TestRoomStayRepository:
    async def test_find_ids_due_for_checkout(self, test_session):
        """체크아웃 대상 조회 쿼리 테스트"""
        repository = SqlAlchemyRoomStayRepository(test_session)
        # 데이터가 없으므로 빈 리스트 반환 확인
        result = await repository.find_ids_due_for_checkout(10)
        assert isinstance(result, list)

    async def test_find_ids_due_for_reminder(self, test_session):
        """리마인더 대상 조회 쿼리 테스트"""
        repository = SqlAlchemyRoomStayRepository(test_session)
        result = await repository.find_ids_due_for_reminder(10)
        assert isinstance(result, list)

    async def test_find_checked_in_by_user_id_with_duplicates(self, test_session, setup_dependencies):
        """중복된 Active Stay가 있을 때 최신 것 하나만 반환하는지 테스트"""
        repository = SqlAlchemyRoomStayRepository(test_session)
        deps = setup_dependencies
        user_id = deps["user_id"]

        # Old active stay
        old_stay = RoomStayModel(
            room_stay_id=Id().value,
            user_id=user_id,
            city_id=deps["city_id"],
            guest_house_id=deps["gh_id"],
            room_id=deps["room_id"],
            ticket_id=deps["ticket_id"],
            status=RoomStayStatus.CHECKED_IN.value,
            check_in_at=datetime.now() - timedelta(hours=2),
            scheduled_check_out_at=datetime.now() + timedelta(hours=22),
            extension_count=0,
            is_checkout_reminder_sent=False,
        )
        test_session.add(old_stay)

        # New active stay (Simulating corruption or race condition)
        new_stay_id = Id().value
        new_stay = RoomStayModel(
            room_stay_id=new_stay_id,
            user_id=user_id,
            city_id=deps["city_id"],
            guest_house_id=deps["gh_id"],
            room_id=deps["room_id"],
            ticket_id=deps["ticket_id"],
            status=RoomStayStatus.CHECKED_IN.value,
            check_in_at=datetime.now(),  # More recent
            scheduled_check_out_at=datetime.now() + timedelta(hours=24),
            extension_count=0,
            is_checkout_reminder_sent=False,
        )
        test_session.add(new_stay)
        await test_session.flush()

        # Act & Assert
        # Should NOT raise MultipleResultsFound
        # Should return the 'new_stay' because check_in_at is later
        result = await repository.find_checked_in_by_user_id(Id(user_id))

        assert result is not None
        assert result.room_stay_id == Id(new_stay_id)
