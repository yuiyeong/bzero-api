from datetime import datetime
from typing import Any

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.core.settings import get_settings
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.ticket import TicketStatus
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel


@pytest_asyncio.fixture
async def sample_city(test_session: AsyncSession) -> CityModel:
    """테스트용 도시 데이터 생성"""
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
        created_at=datetime.now(get_settings().timezone),
        updated_at=datetime.now(get_settings().timezone),
    )
    test_session.add(city)
    await test_session.commit()
    await test_session.refresh(city)
    return city


@pytest_asyncio.fixture
async def sample_airship(test_session: AsyncSession) -> AirshipModel:
    """테스트용 비행선 데이터 생성"""
    airship = AirshipModel(
        airship_id=Id().value,
        name="일반 비행선",
        description="편안한 속도로 여행하는 일반 비행선입니다.",
        image_url="https://example.com/normal_airship.jpg",
        cost_factor=1,
        duration_factor=1,
        display_order=1,
        is_active=True,
        created_at=datetime.now(get_settings().timezone),
        updated_at=datetime.now(get_settings().timezone),
    )
    test_session.add(airship)
    await test_session.commit()
    await test_session.refresh(airship)
    return airship


@pytest_asyncio.fixture
async def expensive_airship(test_session: AsyncSession) -> AirshipModel:
    """비용이 높은 테스트용 비행선 데이터 생성"""
    airship = AirshipModel(
        airship_id=Id().value,
        name="쾌속 비행선",
        description="빠른 속도로 이동할 수 있는 쾌속 비행선입니다.",
        image_url="https://example.com/express_airship.jpg",
        cost_factor=20,  # 매우 높은 비용
        duration_factor=1,
        display_order=2,
        is_active=True,
        created_at=datetime.now(get_settings().timezone),
        updated_at=datetime.now(get_settings().timezone),
    )
    test_session.add(airship)
    await test_session.commit()
    await test_session.refresh(airship)
    return airship


@pytest_asyncio.fixture
async def inactive_city(test_session: AsyncSession) -> CityModel:
    """비활성 테스트용 도시 데이터 생성"""
    city = CityModel(
        city_id=Id().value,
        name="비활성 도시",
        theme="테스트",
        description="비활성 테스트 도시",
        image_url=None,
        base_cost_points=100,
        base_duration_hours=1,
        is_active=False,
        display_order=2,
        created_at=datetime.now(get_settings().timezone),
        updated_at=datetime.now(get_settings().timezone),
    )
    test_session.add(city)
    await test_session.commit()
    await test_session.refresh(city)
    return city


@pytest_asyncio.fixture
async def inactive_airship(test_session: AsyncSession) -> AirshipModel:
    """비활성 테스트용 비행선 데이터 생성"""
    airship = AirshipModel(
        airship_id=Id().value,
        name="비활성 비행선",
        description="현재 운행하지 않는 비행선입니다.",
        image_url=None,
        cost_factor=1,
        duration_factor=1,
        display_order=3,
        is_active=False,
        created_at=datetime.now(get_settings().timezone),
        updated_at=datetime.now(get_settings().timezone),
    )
    test_session.add(airship)
    await test_session.commit()
    await test_session.refresh(airship)
    return airship


class TestPurchaseTicket:
    """POST /api/v1/tickets 테스트"""

    async def test_purchase_ticket_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
        sample_airship: AirshipModel,
    ):
        """티켓 구매 성공"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        city_id = sample_city.city_id.hex
        airship_id = sample_airship.airship_id.hex

        # When
        response = await client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={"city_id": city_id, "airship_id": airship_id},
        )

        # Then
        assert response.status_code == 200
        data = response.json()["data"]

        assert "ticket_id" in data
        assert "ticket_number" in data
        assert data["ticket_number"].startswith("B0-")
        assert data["status"] == TicketStatus.BOARDING.value
        assert data["cost_points"] == 100  # base_cost * cost_factor

        # city snapshot
        assert data["city"]["city_id"] == city_id
        assert data["city"]["name"] == "세렌시아"
        assert data["city"]["theme"] == "관계의 도시"

        # airship snapshot
        assert data["airship"]["airship_id"] == airship_id
        assert data["airship"]["name"] == "일반 비행선"

        assert "departure_datetime" in data
        assert "arrival_datetime" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_purchase_ticket_deducts_points(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
        sample_airship: AirshipModel,
    ):
        """티켓 구매 시 포인트가 차감됨"""
        # Given: 사용자 생성 (초기 포인트 1000P)
        await client.post("/api/v1/users/me", headers=auth_headers)

        city_id = sample_city.city_id.hex
        airship_id = sample_airship.airship_id.hex

        # When: 티켓 구매 (100P 차감)
        await client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={"city_id": city_id, "airship_id": airship_id},
        )

        # Then: 포인트가 차감되었는지 확인
        user_response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert user_response.json()["data"]["current_points"] == 900

    async def test_purchase_ticket_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
        sample_airship: AirshipModel,
    ):
        """사용자가 없으면 404 에러"""
        # Given: 사용자를 생성하지 않음
        city_id = sample_city.city_id.hex
        airship_id = sample_airship.airship_id.hex

        # When
        response = await client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={"city_id": city_id, "airship_id": airship_id},
        )

        # Then
        assert response.status_code == 404

    async def test_purchase_ticket_city_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_airship: AirshipModel,
    ):
        """도시가 없으면 404 에러"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        nonexistent_city_id = Id().value.hex
        airship_id = sample_airship.airship_id.hex

        # When
        response = await client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={"city_id": nonexistent_city_id, "airship_id": airship_id},
        )

        # Then
        assert response.status_code == 404

    async def test_purchase_ticket_airship_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
    ):
        """비행선이 없으면 404 에러"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        city_id = sample_city.city_id.hex
        nonexistent_airship_id = Id().value.hex

        # When
        response = await client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={"city_id": city_id, "airship_id": nonexistent_airship_id},
        )

        # Then
        assert response.status_code == 404

    async def test_purchase_ticket_insufficient_points(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
        expensive_airship: AirshipModel,
    ):
        """포인트가 부족하면 400 에러"""
        # Given: 사용자 생성 (초기 포인트 1000P)
        await client.post("/api/v1/users/me", headers=auth_headers)

        city_id = sample_city.city_id.hex
        airship_id = expensive_airship.airship_id.hex
        # cost = 100 * 20 = 2000P > 1000P

        # When
        response = await client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={"city_id": city_id, "airship_id": airship_id},
        )

        # Then
        assert response.status_code == 400

    async def test_purchase_ticket_inactive_city(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        inactive_city: CityModel,
        sample_airship: AirshipModel,
    ):
        """비활성 도시는 구매 불가 400 에러"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        city_id = inactive_city.city_id.hex
        airship_id = sample_airship.airship_id.hex

        # When
        response = await client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={"city_id": city_id, "airship_id": airship_id},
        )

        # Then
        assert response.status_code == 400

    async def test_purchase_ticket_inactive_airship(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
        inactive_airship: AirshipModel,
    ):
        """비활성 비행선은 구매 불가 400 에러"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        city_id = sample_city.city_id.hex
        airship_id = inactive_airship.airship_id.hex

        # When
        response = await client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={"city_id": city_id, "airship_id": airship_id},
        )

        # Then
        assert response.status_code == 400

    async def test_purchase_ticket_unauthorized(
        self,
        client: AsyncClient,
        sample_city: CityModel,
        sample_airship: AirshipModel,
    ):
        """인증 없이 요청하면 403 에러"""
        # When
        response = await client.post(
            "/api/v1/tickets",
            json={
                "city_id": sample_city.city_id.hex,
                "airship_id": sample_airship.airship_id.hex,
            },
        )

        # Then
        assert response.status_code == 403


class TestGetMyTickets:
    """GET /api/v1/tickets/mine 테스트"""

    async def test_get_my_tickets_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
        sample_airship: AirshipModel,
    ):
        """내 티켓 목록 조회 성공"""
        # Given: 사용자 생성 및 티켓 구매
        await client.post("/api/v1/users/me", headers=auth_headers)
        await client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "city_id": sample_city.city_id.hex,
                "airship_id": sample_airship.airship_id.hex,
            },
        )

        # When
        response = await client.get("/api/v1/tickets/mine", headers=auth_headers)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "list" in data
        assert "pagination" in data

        tickets = data["list"]
        pagination = data["pagination"]

        assert len(tickets) == 1
        assert tickets[0]["city"]["name"] == "세렌시아"
        assert tickets[0]["airship"]["name"] == "일반 비행선"

        assert pagination["total"] == 1
        assert pagination["offset"] == 0
        assert pagination["limit"] == 20

    async def test_get_my_tickets_empty_list(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """티켓이 없으면 빈 리스트 반환"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When
        response = await client.get("/api/v1/tickets/mine", headers=auth_headers)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["list"] == []
        assert data["pagination"]["total"] == 0

    async def test_get_my_tickets_with_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
    ):
        """페이지네이션으로 티켓 목록 조회"""
        # Given: 사용자 생성 및 여러 티켓 구매
        await client.post("/api/v1/users/me", headers=auth_headers)

        # 비용이 낮은 도시로 여러 티켓 구매
        sample_city.base_cost_points = 50
        test_session.add(sample_city)
        await test_session.commit()

        for _ in range(3):
            await client.post(
                "/api/v1/tickets",
                headers=auth_headers,
                json={
                    "city_id": sample_city.city_id.hex,
                    "airship_id": sample_airship.airship_id.hex,
                },
            )

        # When
        response = await client.get(
            "/api/v1/tickets/mine?offset=0&limit=2",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()

        assert len(data["list"]) == 2
        assert data["pagination"]["total"] == 3
        assert data["pagination"]["offset"] == 0
        assert data["pagination"]["limit"] == 2

    async def test_get_my_tickets_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자가 없으면 404 에러"""
        # When: 사용자 생성 없이 조회
        response = await client.get("/api/v1/tickets/mine", headers=auth_headers)

        # Then
        assert response.status_code == 404

    async def test_get_my_tickets_unauthorized(self, client: AsyncClient):
        """인증 없이 요청하면 403 에러"""
        # When
        response = await client.get("/api/v1/tickets/mine")

        # Then
        assert response.status_code == 403


class TestGetCurrentBoardingTicket:
    """GET /api/v1/tickets/mine/boarding 테스트"""

    async def test_get_current_boarding_ticket_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
        sample_airship: AirshipModel,
    ):
        """현재 탑승 중인 티켓 조회 성공"""
        # Given: 사용자 생성 및 티켓 구매 (구매 직후 boarding 상태)
        await client.post("/api/v1/users/me", headers=auth_headers)
        purchase_response = await client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "city_id": sample_city.city_id.hex,
                "airship_id": sample_airship.airship_id.hex,
            },
        )
        ticket_id = purchase_response.json()["data"]["ticket_id"]

        # When
        response = await client.get(
            "/api/v1/tickets/mine/boarding",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()["data"]

        assert data["ticket_id"] == ticket_id
        assert data["status"] == TicketStatus.BOARDING.value
        assert data["city"]["name"] == "세렌시아"
        assert data["airship"]["name"] == "일반 비행선"

    async def test_get_current_boarding_ticket_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """탑승 중인 티켓이 없으면 404 에러"""
        # Given: 사용자 생성 (티켓 없음)
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When
        response = await client.get(
            "/api/v1/tickets/mine/boarding",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 404

    async def test_get_current_boarding_ticket_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자가 없으면 404 에러"""
        # When: 사용자 생성 없이 조회
        response = await client.get(
            "/api/v1/tickets/mine/boarding",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 404

    async def test_get_current_boarding_ticket_unauthorized(self, client: AsyncClient):
        """인증 없이 요청하면 403 에러"""
        # When
        response = await client.get("/api/v1/tickets/mine/boarding")

        # Then
        assert response.status_code == 403


class TestGetTicketDetail:
    """GET /api/v1/tickets/{ticket_id} 테스트"""

    async def test_get_ticket_detail_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
        sample_airship: AirshipModel,
    ):
        """티켓 상세 조회 성공"""
        # Given: 사용자 생성 및 티켓 구매
        await client.post("/api/v1/users/me", headers=auth_headers)
        purchase_response = await client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "city_id": sample_city.city_id.hex,
                "airship_id": sample_airship.airship_id.hex,
            },
        )
        ticket_id = purchase_response.json()["data"]["ticket_id"]

        # When
        response = await client.get(
            f"/api/v1/tickets/{ticket_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()["data"]

        assert data["ticket_id"] == ticket_id
        assert data["status"] == TicketStatus.BOARDING.value
        assert data["city"]["name"] == "세렌시아"
        assert data["airship"]["name"] == "일반 비행선"
        assert data["cost_points"] == 100
        assert "ticket_number" in data
        assert "departure_datetime" in data
        assert "arrival_datetime" in data

    async def test_get_ticket_detail_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """티켓이 없으면 404 에러"""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        nonexistent_ticket_id = Id().value.hex

        # When
        response = await client.get(
            f"/api/v1/tickets/{nonexistent_ticket_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 404

    async def test_get_ticket_detail_forbidden_other_user(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
        sample_city: CityModel,
        sample_airship: AirshipModel,
    ):
        """다른 사용자의 티켓 조회 시 403 에러"""
        # Given: 사용자1 생성 및 티켓 구매
        headers_user1 = auth_headers_factory(
            provider_user_id="user-1",
            email="user1@example.com",
        )
        await client.post("/api/v1/users/me", headers=headers_user1)
        purchase_response = await client.post(
            "/api/v1/tickets",
            headers=headers_user1,
            json={
                "city_id": sample_city.city_id.hex,
                "airship_id": sample_airship.airship_id.hex,
            },
        )
        ticket_id = purchase_response.json()["data"]["ticket_id"]

        # Given: 사용자2 생성
        headers_user2 = auth_headers_factory(
            provider_user_id="user-2",
            email="user2@example.com",
        )
        await client.post("/api/v1/users/me", headers=headers_user2)

        # When: 사용자2가 사용자1의 티켓 조회 시도
        response = await client.get(
            f"/api/v1/tickets/{ticket_id}",
            headers=headers_user2,
        )

        # Then
        assert response.status_code == 403

    async def test_get_ticket_detail_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자가 없으면 404 에러"""
        # When: 사용자 생성 없이 조회
        nonexistent_ticket_id = Id().value.hex
        response = await client.get(
            f"/api/v1/tickets/{nonexistent_ticket_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 404

    async def test_get_ticket_detail_unauthorized(self, client: AsyncClient):
        """인증 없이 요청하면 403 에러"""
        # When
        ticket_id = Id().value.hex
        response = await client.get(f"/api/v1/tickets/{ticket_id}")

        # Then
        assert response.status_code == 403


class TestTicketFlow:
    """티켓 플로우 통합 테스트"""

    async def test_full_ticket_flow(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city: CityModel,
        sample_airship: AirshipModel,
    ):
        """전체 티켓 플로우 테스트: 사용자 생성 -> 티켓 구매 -> 목록 조회 -> 상세 조회 -> 탑승 중 조회"""
        # 1. 사용자 생성
        user_response = await client.post("/api/v1/users/me", headers=auth_headers)
        assert user_response.status_code == 201
        initial_points = user_response.json()["data"]["current_points"]
        assert initial_points == 1000

        # 2. 티켓 구매
        purchase_response = await client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "city_id": sample_city.city_id.hex,
                "airship_id": sample_airship.airship_id.hex,
            },
        )
        assert purchase_response.status_code == 200
        ticket_data = purchase_response.json()["data"]
        ticket_id = ticket_data["ticket_id"]
        cost = ticket_data["cost_points"]

        # 3. 포인트 차감 확인
        user_response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert user_response.json()["data"]["current_points"] == initial_points - cost

        # 4. 티켓 목록 조회
        list_response = await client.get("/api/v1/tickets/mine", headers=auth_headers)
        assert list_response.status_code == 200
        assert len(list_response.json()["list"]) == 1

        # 5. 티켓 상세 조회
        detail_response = await client.get(
            f"/api/v1/tickets/{ticket_id}",
            headers=auth_headers,
        )
        assert detail_response.status_code == 200
        assert detail_response.json()["data"]["ticket_id"] == ticket_id

        # 6. 탑승 중인 티켓 조회
        boarding_response = await client.get(
            "/api/v1/tickets/mine/boarding",
            headers=auth_headers,
        )
        assert boarding_response.status_code == 200
        assert boarding_response.json()["data"]["ticket_id"] == ticket_id

    async def test_multiple_users_ticket_isolation(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
        sample_city: CityModel,
        sample_airship: AirshipModel,
    ):
        """다른 사용자의 티켓은 서로 격리됨"""
        # Given: 두 명의 사용자 생성
        headers_user1 = auth_headers_factory(
            provider_user_id="user-1",
            email="user1@example.com",
        )
        headers_user2 = auth_headers_factory(
            provider_user_id="user-2",
            email="user2@example.com",
        )

        await client.post("/api/v1/users/me", headers=headers_user1)
        await client.post("/api/v1/users/me", headers=headers_user2)

        # When: 각각 티켓 구매
        await client.post(
            "/api/v1/tickets",
            headers=headers_user1,
            json={
                "city_id": sample_city.city_id.hex,
                "airship_id": sample_airship.airship_id.hex,
            },
        )

        # Then: 각 사용자는 자신의 티켓만 조회 가능
        list_response1 = await client.get("/api/v1/tickets/mine", headers=headers_user1)
        list_response2 = await client.get("/api/v1/tickets/mine", headers=headers_user2)

        assert len(list_response1.json()["list"]) == 1
        assert len(list_response2.json()["list"]) == 0
