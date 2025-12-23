"""일기 API E2E 테스트."""

from datetime import datetime, timedelta
from typing import Any

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
from bzero.infrastructure.db.diary_model import DiaryModel
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
# Tests: POST /api/v1/diaries
# =============================================================================


class TestCreateDiary:
    """POST /api/v1/diaries 테스트."""

    async def test_create_diary_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """일기 작성 성공."""
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
        response = await client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "title": "오늘의 일기",
                "content": "오늘 하루도 평화로웠다.",
                "mood": "peaceful",
            },
        )

        # Then
        assert response.status_code == 201
        data = response.json()["data"]

        assert "diary_id" in data
        assert data["user_id"] == user_id
        assert data["room_stay_id"] == room_stay.room_stay_id.hex
        assert data["city_id"] == sample_city.city_id.hex
        assert data["guest_house_id"] == sample_guest_house.guest_house_id.hex
        assert data["title"] == "오늘의 일기"
        assert data["content"] == "오늘 하루도 평화로웠다."
        assert data["mood"] == "peaceful"
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_diary_earns_points(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """일기 작성 시 50P 지급."""
        # Given: 사용자 생성 (초기 1000P)
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]
        initial_points = response.json()["data"]["current_points"]

        # 사용자 모델 조회
        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        # 체류 생성
        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        # When: 일기 작성
        await client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "title": "오늘의 일기",
                "content": "오늘 하루도 평화로웠다.",
                "mood": "peaceful",
            },
        )

        # Then: 50P 지급 확인
        user_response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert user_response.json()["data"]["current_points"] == initial_points + 50

    async def test_create_diary_fails_when_not_staying(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """체류 중이 아닐 때 일기 작성 실패."""
        # Given: 사용자 생성 (체류 없음)
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When
        response = await client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "title": "오늘의 일기",
                "content": "오늘 하루도 평화로웠다.",
                "mood": "peaceful",
            },
        )

        # Then
        assert response.status_code == 404

    async def test_create_diary_fails_when_already_written(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """이미 일기가 작성된 체류에 재작성 시도하면 실패."""
        # Given: 사용자 생성 및 체류 생성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        # 첫 번째 일기 작성
        await client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "title": "첫 번째 일기",
                "content": "오늘 하루도 평화로웠다.",
                "mood": "peaceful",
            },
        )

        # When: 두 번째 일기 작성 시도
        response = await client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "title": "두 번째 일기",
                "content": "또 쓰려고 했는데...",
                "mood": "sad",
            },
        )

        # Then
        assert response.status_code == 409

    async def test_create_diary_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자가 없으면 404 에러."""
        # When: 사용자 생성 없이 일기 작성 시도
        response = await client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "title": "오늘의 일기",
                "content": "오늘 하루도 평화로웠다.",
                "mood": "peaceful",
            },
        )

        # Then
        assert response.status_code == 404

    async def test_create_diary_unauthorized(self, client: AsyncClient):
        """인증 없이 요청하면 403 에러."""
        # When
        response = await client.post(
            "/api/v1/diaries",
            json={
                "title": "오늘의 일기",
                "content": "오늘 하루도 평화로웠다.",
                "mood": "peaceful",
            },
        )

        # Then
        assert response.status_code == 403

    async def test_create_diary_with_all_moods(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
    ):
        """모든 감정 상태로 일기 작성 가능."""
        moods = [
            "happy",
            "peaceful",
            "grateful",
            "reflective",
            "sad",
            "anxious",
            "hopeful",
            "tired",
        ]

        for i, mood in enumerate(moods):
            # Given: 각 테스트마다 새 사용자
            headers = auth_headers_factory(
                provider_user_id=f"user-{i}",
                email=f"user{i}@example.com",
            )
            response = await client.post("/api/v1/users/me", headers=headers)
            user_id = response.json()["data"]["user_id"]

            result = await test_session.execute(
                select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value)
            )
            user_model = result.scalar_one()

            # 새 룸 생성
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

            await create_user_with_room_stay(
                test_session,
                user_model,
                sample_city,
                sample_airship,
                sample_guest_house,
                room,
            )

            # When
            response = await client.post(
                "/api/v1/diaries",
                headers=headers,
                json={
                    "title": f"일기-{mood}",
                    "content": f"{mood} 상태의 일기입니다.",
                    "mood": mood,
                },
            )

            # Then
            assert response.status_code == 201
            assert response.json()["data"]["mood"] == mood


# =============================================================================
# Tests: GET /api/v1/diaries
# =============================================================================


class TestGetMyDiaries:
    """GET /api/v1/diaries 테스트."""

    async def test_get_my_diaries_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """내 일기 목록 조회 성공."""
        # Given: 사용자 생성 및 일기 작성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        await client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "title": "오늘의 일기",
                "content": "오늘 하루도 평화로웠다.",
                "mood": "peaceful",
            },
        )

        # When
        response = await client.get("/api/v1/diaries", headers=auth_headers)

        # Then
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data

        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "오늘의 일기"
        assert data["total"] == 1
        assert data["offset"] == 0
        assert data["limit"] == 20

    async def test_get_my_diaries_empty_list(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """일기가 없으면 빈 리스트 반환."""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When
        response = await client.get("/api/v1/diaries", headers=auth_headers)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_get_my_diaries_with_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
    ):
        """페이지네이션으로 일기 목록 조회."""
        # Given: 사용자 생성 및 여러 일기 작성 (여러 체류 필요)
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        # 3개의 일기 생성 (3개의 다른 room_stay 필요)
        now = datetime.now(get_settings().timezone)
        for i in range(3):
            room = RoomModel(
                room_id=Id().value,
                guest_house_id=sample_guest_house.guest_house_id,
                max_capacity=6,
                current_capacity=0,
                created_at=now,
                updated_at=now,
            )
            test_session.add(room)
            await test_session.flush()

            room_stay = await create_user_with_room_stay(
                test_session,
                user_model,
                sample_city,
                sample_airship,
                sample_guest_house,
                room,
            )

            # DB에 직접 일기 생성
            diary = DiaryModel(
                diary_id=Id().value,
                user_id=user_model.user_id,
                room_stay_id=room_stay.room_stay_id,
                city_id=sample_city.city_id,
                guest_house_id=sample_guest_house.guest_house_id,
                title=f"일기 {i + 1}",
                content=f"내용 {i + 1}",
                mood="peaceful",
                created_at=now + timedelta(minutes=i),
                updated_at=now + timedelta(minutes=i),
            )
            test_session.add(diary)

            # 다음 체류를 위해 현재 체류 체크아웃
            room_stay.status = RoomStayStatus.CHECKED_OUT.value
            room_stay.actual_check_out_at = now + timedelta(minutes=i)

        await test_session.commit()

        # When
        response = await client.get(
            "/api/v1/diaries?offset=0&limit=2",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["offset"] == 0
        assert data["limit"] == 2

    async def test_get_my_diaries_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자가 없으면 404 에러."""
        # When: 사용자 생성 없이 조회
        response = await client.get("/api/v1/diaries", headers=auth_headers)

        # Then
        assert response.status_code == 404

    async def test_get_my_diaries_unauthorized(self, client: AsyncClient):
        """인증 없이 요청하면 403 에러."""
        # When
        response = await client.get("/api/v1/diaries")

        # Then
        assert response.status_code == 403


# =============================================================================
# Tests: GET /api/v1/diaries/{diary_id}
# =============================================================================


class TestGetDiaryDetail:
    """GET /api/v1/diaries/{diary_id} 테스트."""

    async def test_get_diary_detail_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """일기 상세 조회 성공."""
        # Given: 사용자 생성 및 일기 작성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        create_response = await client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "title": "오늘의 일기",
                "content": "오늘 하루도 평화로웠다.",
                "mood": "peaceful",
            },
        )
        diary_id = create_response.json()["data"]["diary_id"]

        # When
        response = await client.get(
            f"/api/v1/diaries/{diary_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()["data"]

        assert data["diary_id"] == diary_id
        assert data["title"] == "오늘의 일기"
        assert data["content"] == "오늘 하루도 평화로웠다."
        assert data["mood"] == "peaceful"

    async def test_get_diary_detail_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """일기가 없으면 404 에러."""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        nonexistent_diary_id = Id().value.hex

        # When
        response = await client.get(
            f"/api/v1/diaries/{nonexistent_diary_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 404

    async def test_get_diary_detail_forbidden_other_user(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """다른 사용자의 일기 조회 시 403 에러."""
        # Given: 사용자1 생성 및 일기 작성
        headers_user1 = auth_headers_factory(
            provider_user_id="user-1",
            email="user1@example.com",
        )
        response = await client.post("/api/v1/users/me", headers=headers_user1)
        user1_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user1_id).value))
        user1_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user1_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        create_response = await client.post(
            "/api/v1/diaries",
            headers=headers_user1,
            json={
                "title": "사용자1의 일기",
                "content": "비밀 내용입니다.",
                "mood": "peaceful",
            },
        )
        diary_id = create_response.json()["data"]["diary_id"]

        # Given: 사용자2 생성
        headers_user2 = auth_headers_factory(
            provider_user_id="user-2",
            email="user2@example.com",
        )
        await client.post("/api/v1/users/me", headers=headers_user2)

        # When: 사용자2가 사용자1의 일기 조회 시도
        response = await client.get(
            f"/api/v1/diaries/{diary_id}",
            headers=headers_user2,
        )

        # Then
        assert response.status_code == 403

    async def test_get_diary_detail_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자가 없으면 404 에러."""
        # When: 사용자 생성 없이 조회
        nonexistent_diary_id = Id().value.hex
        response = await client.get(
            f"/api/v1/diaries/{nonexistent_diary_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 404

    async def test_get_diary_detail_unauthorized(self, client: AsyncClient):
        """인증 없이 요청하면 403 에러."""
        # When
        diary_id = Id().value.hex
        response = await client.get(f"/api/v1/diaries/{diary_id}")

        # Then
        assert response.status_code == 403


# =============================================================================
# Tests: PATCH /api/v1/diaries/{diary_id}
# =============================================================================


class TestUpdateDiary:
    """PATCH /api/v1/diaries/{diary_id} 테스트."""

    async def test_update_diary_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """일기 수정 성공."""
        # Given: 사용자 생성 및 일기 작성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        create_response = await client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "title": "오늘의 일기",
                "content": "오늘 하루도 평화로웠다.",
                "mood": "peaceful",
            },
        )
        diary_id = create_response.json()["data"]["diary_id"]

        # When
        response = await client.patch(
            f"/api/v1/diaries/{diary_id}",
            headers=auth_headers,
            json={
                "title": "수정된 제목",
                "content": "수정된 내용입니다.",
                "mood": "happy",
            },
        )

        # Then
        assert response.status_code == 200
        data = response.json()["data"]

        assert data["diary_id"] == diary_id
        assert data["title"] == "수정된 제목"
        assert data["content"] == "수정된 내용입니다."
        assert data["mood"] == "happy"

    async def test_update_diary_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """일기가 없으면 404 에러."""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        nonexistent_diary_id = Id().value.hex

        # When
        response = await client.patch(
            f"/api/v1/diaries/{nonexistent_diary_id}",
            headers=auth_headers,
            json={
                "title": "수정된 제목",
                "content": "수정된 내용입니다.",
                "mood": "happy",
            },
        )

        # Then
        assert response.status_code == 404

    async def test_update_diary_forbidden_other_user(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """다른 사용자의 일기 수정 시 403 에러."""
        # Given: 사용자1 생성 및 일기 작성
        headers_user1 = auth_headers_factory(
            provider_user_id="user-1",
            email="user1@example.com",
        )
        response = await client.post("/api/v1/users/me", headers=headers_user1)
        user1_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user1_id).value))
        user1_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user1_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        create_response = await client.post(
            "/api/v1/diaries",
            headers=headers_user1,
            json={
                "title": "사용자1의 일기",
                "content": "비밀 내용입니다.",
                "mood": "peaceful",
            },
        )
        diary_id = create_response.json()["data"]["diary_id"]

        # Given: 사용자2 생성
        headers_user2 = auth_headers_factory(
            provider_user_id="user-2",
            email="user2@example.com",
        )
        await client.post("/api/v1/users/me", headers=headers_user2)

        # When: 사용자2가 사용자1의 일기 수정 시도
        response = await client.patch(
            f"/api/v1/diaries/{diary_id}",
            headers=headers_user2,
            json={
                "title": "수정된 제목",
                "content": "수정된 내용입니다.",
                "mood": "happy",
            },
        )

        # Then
        assert response.status_code == 403

    async def test_update_diary_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자가 없으면 404 에러."""
        # When: 사용자 생성 없이 수정 시도
        nonexistent_diary_id = Id().value.hex
        response = await client.patch(
            f"/api/v1/diaries/{nonexistent_diary_id}",
            headers=auth_headers,
            json={
                "title": "수정된 제목",
                "content": "수정된 내용입니다.",
                "mood": "happy",
            },
        )

        # Then
        assert response.status_code == 404

    async def test_update_diary_unauthorized(self, client: AsyncClient):
        """인증 없이 요청하면 403 에러."""
        # When
        diary_id = Id().value.hex
        response = await client.patch(
            f"/api/v1/diaries/{diary_id}",
            json={
                "title": "수정된 제목",
                "content": "수정된 내용입니다.",
                "mood": "happy",
            },
        )

        # Then
        assert response.status_code == 403


# =============================================================================
# Tests: DELETE /api/v1/diaries/{diary_id}
# =============================================================================


class TestDeleteDiary:
    """DELETE /api/v1/diaries/{diary_id} 테스트."""

    async def test_delete_diary_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """일기 삭제 성공 (soft delete)."""
        # Given: 사용자 생성 및 일기 작성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        create_response = await client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "title": "오늘의 일기",
                "content": "오늘 하루도 평화로웠다.",
                "mood": "peaceful",
            },
        )
        diary_id = create_response.json()["data"]["diary_id"]

        # When
        response = await client.delete(
            f"/api/v1/diaries/{diary_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 204

        # 삭제 후 조회 불가 확인
        get_response = await client.get(
            f"/api/v1/diaries/{diary_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_delete_diary_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """일기가 없으면 404 에러."""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        nonexistent_diary_id = Id().value.hex

        # When
        response = await client.delete(
            f"/api/v1/diaries/{nonexistent_diary_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 404

    async def test_delete_diary_forbidden_other_user(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """다른 사용자의 일기 삭제 시 403 에러."""
        # Given: 사용자1 생성 및 일기 작성
        headers_user1 = auth_headers_factory(
            provider_user_id="user-1",
            email="user1@example.com",
        )
        response = await client.post("/api/v1/users/me", headers=headers_user1)
        user1_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user1_id).value))
        user1_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user1_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        create_response = await client.post(
            "/api/v1/diaries",
            headers=headers_user1,
            json={
                "title": "사용자1의 일기",
                "content": "비밀 내용입니다.",
                "mood": "peaceful",
            },
        )
        diary_id = create_response.json()["data"]["diary_id"]

        # Given: 사용자2 생성
        headers_user2 = auth_headers_factory(
            provider_user_id="user-2",
            email="user2@example.com",
        )
        await client.post("/api/v1/users/me", headers=headers_user2)

        # When: 사용자2가 사용자1의 일기 삭제 시도
        response = await client.delete(
            f"/api/v1/diaries/{diary_id}",
            headers=headers_user2,
        )

        # Then
        assert response.status_code == 403

    async def test_delete_diary_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자가 없으면 404 에러."""
        # When: 사용자 생성 없이 삭제 시도
        nonexistent_diary_id = Id().value.hex
        response = await client.delete(
            f"/api/v1/diaries/{nonexistent_diary_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 404

    async def test_delete_diary_unauthorized(self, client: AsyncClient):
        """인증 없이 요청하면 403 에러."""
        # When
        diary_id = Id().value.hex
        response = await client.delete(f"/api/v1/diaries/{diary_id}")

        # Then
        assert response.status_code == 403


# =============================================================================
# Tests: 일기 플로우 통합 테스트
# =============================================================================


class TestDiaryFlow:
    """일기 플로우 통합 테스트."""

    async def test_full_diary_flow(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """전체 일기 플로우 테스트: 생성 -> 조회 -> 수정 -> 삭제."""
        # 1. 사용자 생성
        user_response = await client.post("/api/v1/users/me", headers=auth_headers)
        assert user_response.status_code == 201
        user_id = user_response.json()["data"]["user_id"]
        initial_points = user_response.json()["data"]["current_points"]

        # 체류 생성
        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        # 2. 일기 작성
        create_response = await client.post(
            "/api/v1/diaries",
            headers=auth_headers,
            json={
                "title": "오늘의 일기",
                "content": "오늘 하루도 평화로웠다.",
                "mood": "peaceful",
            },
        )
        assert create_response.status_code == 201
        diary_id = create_response.json()["data"]["diary_id"]

        # 3. 포인트 지급 확인
        user_response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert user_response.json()["data"]["current_points"] == initial_points + 50

        # 4. 일기 목록 조회
        list_response = await client.get("/api/v1/diaries", headers=auth_headers)
        assert list_response.status_code == 200
        assert len(list_response.json()["items"]) == 1

        # 5. 일기 상세 조회
        detail_response = await client.get(
            f"/api/v1/diaries/{diary_id}",
            headers=auth_headers,
        )
        assert detail_response.status_code == 200
        assert detail_response.json()["data"]["diary_id"] == diary_id

        # 6. 일기 수정
        update_response = await client.patch(
            f"/api/v1/diaries/{diary_id}",
            headers=auth_headers,
            json={
                "title": "수정된 제목",
                "content": "수정된 내용입니다.",
                "mood": "happy",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["title"] == "수정된 제목"

        # 7. 일기 삭제
        delete_response = await client.delete(
            f"/api/v1/diaries/{diary_id}",
            headers=auth_headers,
        )
        assert delete_response.status_code == 204

        # 8. 삭제 후 조회 불가 확인
        get_response = await client.get(
            f"/api/v1/diaries/{diary_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_multiple_users_diary_isolation(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
    ):
        """다른 사용자의 일기는 서로 격리됨."""
        now = datetime.now(get_settings().timezone)

        # Given: 두 명의 사용자 생성
        headers_user1 = auth_headers_factory(
            provider_user_id="user-1",
            email="user1@example.com",
        )
        headers_user2 = auth_headers_factory(
            provider_user_id="user-2",
            email="user2@example.com",
        )

        response1 = await client.post("/api/v1/users/me", headers=headers_user1)
        response2 = await client.post("/api/v1/users/me", headers=headers_user2)

        user1_id = response1.json()["data"]["user_id"]
        user2_id = response2.json()["data"]["user_id"]

        # 각 사용자 모델 조회
        result1 = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user1_id).value))
        user1_model = result1.scalar_one()

        result2 = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user2_id).value))
        user2_model = result2.scalar_one()

        # 각 사용자별 룸 및 체류 생성
        room1 = RoomModel(
            room_id=Id().value,
            guest_house_id=sample_guest_house.guest_house_id,
            max_capacity=6,
            current_capacity=0,
            created_at=now,
            updated_at=now,
        )
        room2 = RoomModel(
            room_id=Id().value,
            guest_house_id=sample_guest_house.guest_house_id,
            max_capacity=6,
            current_capacity=0,
            created_at=now,
            updated_at=now,
        )
        test_session.add(room1)
        test_session.add(room2)
        await test_session.commit()
        await test_session.refresh(room1)
        await test_session.refresh(room2)

        await create_user_with_room_stay(
            test_session,
            user1_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            room1,
        )

        await create_user_with_room_stay(
            test_session,
            user2_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            room2,
        )

        # When: 사용자1만 일기 작성
        await client.post(
            "/api/v1/diaries",
            headers=headers_user1,
            json={
                "title": "사용자1의 일기",
                "content": "오늘 하루도 평화로웠다.",
                "mood": "peaceful",
            },
        )

        # Then: 각 사용자는 자신의 일기만 조회 가능
        list_response1 = await client.get("/api/v1/diaries", headers=headers_user1)
        list_response2 = await client.get("/api/v1/diaries", headers=headers_user2)

        assert len(list_response1.json()["items"]) == 1
        assert len(list_response2.json()["items"]) == 0
