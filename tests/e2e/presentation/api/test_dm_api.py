from datetime import datetime, timedelta
from typing import Any

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.room_stay import RoomStayStatus
from bzero.domain.value_objects.ticket import TicketStatus
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.direct_message_model import DirectMessageModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.room_model import RoomModel
from bzero.infrastructure.db.room_stay_model import RoomStayModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_identity_model import UserIdentityModel
from bzero.infrastructure.db.user_model import UserModel


# =============================================================================
# Fixtures (Copied/Adapted from test_room_api.py)
# =============================================================================

@pytest_asyncio.fixture
async def sample_city(test_session: AsyncSession) -> CityModel:
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

async def create_user_with_identity(
    test_session: AsyncSession,
    provider: str,
    provider_user_id: str,
    email: str,
    nickname: str | None = None,
) -> UserModel:
    now = datetime.now(get_settings().timezone)
    user = UserModel(
        user_id=Id().value,
        email=email,
        nickname=nickname or f"유저{uuid7().hex}",
        profile_emoji="🙂",
        current_points=1000,
        created_at=now,
        updated_at=now,
    )
    test_session.add(user)
    await test_session.flush()

    identity = UserIdentityModel(
        identity_id=Id().value,
        user_id=user.user_id,
        provider=provider,
        provider_user_id=provider_user_id,
        created_at=now,
        updated_at=now,
    )
    test_session.add(identity)
    await test_session.commit()
    await test_session.refresh(user)
    return user

async def create_room_stay_for_user(
    test_session: AsyncSession,
    user_model: UserModel,
    sample_city: CityModel,
    sample_airship: AirshipModel,
    sample_guest_house: GuestHouseModel,
    sample_room: RoomModel,
) -> RoomStayModel:
    now = datetime.now(get_settings().timezone)

    ticket = TicketModel(
        ticket_id=Id().value,
        user_id=user_model.user_id,
        ticket_number=f"B0-TEST-{uuid7().hex[:13]}",
        city_id=sample_city.city_id,
        city_name=sample_city.name,
        city_theme=sample_city.theme,
        city_description=sample_city.description,
        city_image_url=sample_city.image_url,
        city_base_cost_points=sample_city.base_cost_points,
        city_base_duration_hours=sample_city.base_duration_hours,
        airship_id=sample_airship.airship_id,
        airship_name=sample_airship.name,
        airship_description=sample_airship.description,
        airship_image_url=sample_airship.image_url,
        airship_cost_factor=sample_airship.cost_factor,
        airship_duration_factor=sample_airship.duration_factor,
        cost_points=100,
        status=TicketStatus.COMPLETED.value,
        departure_datetime=now - timedelta(hours=1),
        arrival_datetime=now,
        created_at=now,
        updated_at=now,
    )
    test_session.add(ticket)
    await test_session.flush()

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
# E2E Tests for DM
# =============================================================================

class TestDirectMessageApi:
    """DM 관련 API E2E 테스트."""

    async def test_create_dm_room_success(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """DM방 생성 성공 시나리오."""
        # 1. 두 명의 유저 생성
        user1 = await create_user_with_identity(test_session, "email", "u1", "u1@e.com", "User1")
        user2 = await create_user_with_identity(test_session, "email", "u2", "u2@e.com", "User2")

        # 2. 두 유저 모두 같은 방에 입장 (RoomStay)
        await create_room_stay_for_user(test_session, user1, sample_city, sample_airship, sample_guest_house, sample_room)
        await create_room_stay_for_user(test_session, user2, sample_city, sample_airship, sample_guest_house, sample_room)

        # 3. User1 로그인 헤더
        headers = auth_headers_factory(provider="email", provider_user_id="u1", email="u1@e.com")

        # 4. DM 방 생성 요청 (User1 -> User2)
        # Endpoint: POST /api/v1/dm/requests
        payload = {"to_user_id": str(user2.user_id)}
        response = await client.post("/api/v1/dm/requests", headers=headers, json=payload)

        if response.status_code not in (200, 201):
            print(f"DEBUG: Response Error: {response.json()}")

        assert response.status_code in (200, 201)
        data = response.json()
        assert data["dm_room_id"] is not None
        assert data["user1_id"].replace("-", "") == str(user1.user_id).replace("-", "")
        assert data["user2_id"].replace("-", "") == str(user2.user_id).replace("-", "")
        assert data["status"] == "pending"

        return data["dm_room_id"]

    async def test_dm_lifecycle(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """DM 요청 -> 수락 -> 목록 조회 -> 메시지 조회(시드) 시나리오."""

        # 1. 유저 및 방 생성, 입장
        user1 = await create_user_with_identity(test_session, "email", "u1m", "u1m@e.com", "User1Msg")
        user2 = await create_user_with_identity(test_session, "email", "u2m", "u2m@e.com", "User2Msg")

        await create_room_stay_for_user(test_session, user1, sample_city, sample_airship, sample_guest_house, sample_room)
        await create_room_stay_for_user(test_session, user2, sample_city, sample_airship, sample_guest_house, sample_room)

        # 2. DM 요청 (User1 -> User2)
        headers1 = auth_headers_factory(provider="email", provider_user_id="u1m", email="u1m@e.com")
        create_resp = await client.post(
            "/api/v1/dm/requests",
            headers=headers1,
            json={"to_user_id": str(user2.user_id)}
        )
        assert create_resp.status_code in (200, 201)
        dm_room_id = create_resp.json()["dm_room_id"]

        # 3. DM 수락 (User2)
        headers2 = auth_headers_factory(provider="email", provider_user_id="u2m", email="u2m@e.com")
        accept_resp = await client.post(
            f"/api/v1/dm/requests/{dm_room_id}/accept",
            headers=headers2
        )
        assert accept_resp.status_code == 200
        assert accept_resp.json()["status"] == "accepted"

        # 4. DM 방 목록 조회 (User1)
        list_resp = await client.get("/api/v1/dm/rooms", headers=headers1)
        assert list_resp.status_code == 200
        rooms = list_resp.json()["list"]
        assert len(rooms) >= 1
        assert rooms[0]["dm_room_id"] == dm_room_id
        assert rooms[0]["status"] == "accepted"

        # 5. 메시지 수동 시드 (REST API로는 메시지 전송 불가 가정)
        now = datetime.now(get_settings().timezone)
        message = DirectMessageModel(
            dm_id=Id().value,
            dm_room_id=Id.from_hex(dm_room_id).value,
            from_user_id=user1.user_id,
            to_user_id=user2.user_id,
            content="Hello Seeded Message!",
            is_read=False,
            created_at=now,
            updated_at=now,
        )
        test_session.add(message)
        await test_session.commit()

        # 6. 메시지 조회 (User2)
        history_resp = await client.get(
             f"/api/v1/dm/rooms/{dm_room_id}/messages",
             headers=headers2
        )
        assert history_resp.status_code == 200
        history_data = history_resp.json()
        assert len(history_data["list"]) >= 1
        assert history_data["list"][0]["content"] == "Hello Seeded Message!"
