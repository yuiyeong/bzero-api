from datetime import datetime, timedelta

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.room_stay import RoomStayStatus
from bzero.domain.value_objects.ticket import TicketStatus
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.room_model import RoomModel
from bzero.infrastructure.db.room_stay_model import RoomStayModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_model import UserModel


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def sample_city(test_session: AsyncSession) -> CityModel:
    """테스트용 도시 데이터 생성."""
    now = datetime.now(get_settings().timezone)
    city = CityModel(
        city_id=Id().value,
        name="세렌시아",
        theme="관계의 도시",
        description="관계에 대해 생각하는 도시",
        image_url="https://example.com/serencia.jpg",
        base_cost_points=100,
        base_duration_hours=1,
        is_active=True,
        display_order=1,
        created_at=now,
        updated_at=now,
    )
    test_session.add(city)
    await test_session.commit()
    await test_session.refresh(city)
    return city


@pytest_asyncio.fixture
async def sample_airship(test_session: AsyncSession) -> AirshipModel:
    """테스트용 비행선 데이터 생성."""
    now = datetime.now(get_settings().timezone)
    airship = AirshipModel(
        airship_id=Id().value,
        name="일반 비행선",
        description="편안한 속도로 여행하는 일반 비행선입니다.",
        image_url="https://example.com/normal_airship.jpg",
        cost_factor=1,
        duration_factor=1,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(airship)
    await test_session.commit()
    await test_session.refresh(airship)
    return airship


@pytest_asyncio.fixture
async def sample_guest_house(
    test_session: AsyncSession,
    sample_city: CityModel,
) -> GuestHouseModel:
    """테스트용 게스트하우스 데이터 생성."""
    now = datetime.now(get_settings().timezone)
    guest_house = GuestHouseModel(
        guest_house_id=Id().value,
        city_id=sample_city.city_id,
        guest_house_type="mixed",
        name="혼합형 게스트하우스",
        description="대화를 나눌 수 있는 공간",
        image_url="https://example.com/mixed.jpg",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(guest_house)
    await test_session.commit()
    await test_session.refresh(guest_house)
    return guest_house


@pytest_asyncio.fixture
async def sample_room(
    test_session: AsyncSession,
    sample_guest_house: GuestHouseModel,
) -> RoomModel:
    """테스트용 룸 데이터 생성."""
    now = datetime.now(get_settings().timezone)
    room = RoomModel(
        room_id=Id().value,
        guest_house_id=sample_guest_house.guest_house_id,
        max_capacity=6,
        current_capacity=0,
        created_at=now,
        updated_at=now,
    )
    test_session.add(room)
    await test_session.commit()
    await test_session.refresh(room)
    return room


async def create_user_with_room_stay(
    test_session: AsyncSession,
    user_model: UserModel,
    sample_city: CityModel,
    sample_airship: AirshipModel,
    sample_guest_house: GuestHouseModel,
    sample_room: RoomModel,
) -> RoomStayModel:
    """사용자에 대한 체류 데이터를 생성합니다."""
    now = datetime.now(get_settings().timezone)

    # 완료된 티켓 생성
    ticket = TicketModel(
        ticket_id=Id().value,
        user_id=user_model.user_id,
        ticket_number=f"B0-TEST-{uuid7().hex[:13]}",
        # City snapshot fields
        city_id=sample_city.city_id,
        city_name=sample_city.name,
        city_theme=sample_city.theme,
        city_description=sample_city.description,
        city_image_url=sample_city.image_url,
        city_base_cost_points=sample_city.base_cost_points,
        city_base_duration_hours=sample_city.base_duration_hours,
        # Airship snapshot fields
        airship_id=sample_airship.airship_id,
        airship_name=sample_airship.name,
        airship_description=sample_airship.description,
        airship_image_url=sample_airship.image_url,
        airship_cost_factor=sample_airship.cost_factor,
        airship_duration_factor=sample_airship.duration_factor,
        # Ticket fields
        cost_points=100,
        status=TicketStatus.COMPLETED.value,
        departure_datetime=now - timedelta(hours=1),
        arrival_datetime=now,
        created_at=now,
        updated_at=now,
    )
    test_session.add(ticket)
    await test_session.flush()

    # 체류 생성
    room_stay = RoomStayModel(
        room_stay_id=Id().value,
        user_id=user_model.user_id,
        city_id=sample_city.city_id,
        guest_house_id=sample_guest_house.guest_house_id,
        room_id=sample_room.room_id,
        ticket_id=ticket.ticket_id,
        status=RoomStayStatus.CHECKED_IN.value,
        check_in_at=now,
        scheduled_check_out_at=now + timedelta(hours=24),
        actual_check_out_at=None,
        extension_count=0,
        created_at=now,
        updated_at=now,
    )
    test_session.add(room_stay)
    await test_session.commit()
    await test_session.refresh(room_stay)
    return room_stay


# =============================================================================
# Tests
# =============================================================================


class TestGetCurrentStay:
    """GET /api/v1/room-stays/current 테스트."""

    async def test_get_current_stay_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """현재 체류 조회 성공."""
        # Given: 사용자 생성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        # 사용자 모델 조회
        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        # 체류 생성
        room_stay = await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        # When
        response = await client.get("/api/v1/room-stays/current", headers=auth_headers)

        # Then
        assert response.status_code == 200
        data = response.json()["data"]

        assert data["room_stay_id"] == room_stay.room_stay_id.hex
        assert data["user_id"] == user_id
        assert data["city_id"] == sample_city.city_id.hex
        assert data["guest_house_id"] == sample_guest_house.guest_house_id.hex
        assert data["room_id"] == sample_room.room_id.hex
        assert data["status"] == RoomStayStatus.CHECKED_IN.value
        assert data["extension_count"] == 0
        assert "check_in_at" in data
        assert "scheduled_check_out_at" in data
        assert data["actual_check_out_at"] is None

    async def test_get_current_stay_returns_extended_status(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """EXTENDED 상태인 체류도 조회되어야 합니다."""
        # Given: 사용자 생성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        # 사용자 모델 조회
        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        # EXTENDED 상태 체류 생성
        room_stay = await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        # EXTENDED 상태로 변경
        room_stay.status = RoomStayStatus.EXTENDED.value
        room_stay.extension_count = 1
        await test_session.commit()
        await test_session.refresh(room_stay)

        # When
        response = await client.get("/api/v1/room-stays/current", headers=auth_headers)

        # Then
        assert response.status_code == 200
        data = response.json()["data"]

        assert data["room_stay_id"] == room_stay.room_stay_id.hex
        assert data["status"] == RoomStayStatus.EXTENDED.value
        assert data["extension_count"] == 1

    async def test_get_current_stay_returns_none_when_not_staying(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """체류 중이 아닌 경우 None 반환."""
        # Given: 사용자 생성 (체류 없음)
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When
        response = await client.get("/api/v1/room-stays/current", headers=auth_headers)

        # Then
        assert response.status_code == 200
        assert response.json() is None

    async def test_get_current_stay_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자가 없으면 404 에러."""
        # When: 사용자 생성 없이 조회
        response = await client.get("/api/v1/room-stays/current", headers=auth_headers)

        # Then
        assert response.status_code == 404

    async def test_get_current_stay_unauthorized(self, client: AsyncClient):
        """인증 없이 요청하면 403 에러."""
        # When
        response = await client.get("/api/v1/room-stays/current")

        # Then
        assert response.status_code == 403
