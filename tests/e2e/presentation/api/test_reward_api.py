"""Reward API E2E 테스트."""

from typing import Any

from httpx import AsyncClient


class TestClaimDailyLoginReward:
    """POST /api/v1/rewards/daily-login/claim 테스트."""

    async def test_claim_daily_login_first_time_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """첫 번째 일일 출석 보상 수령 시 claimed=True를 반환합니다."""
        # Given: 사용자 생성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 201

        # When: 일일 출석 보상 수령
        response = await client.post(
            "/api/v1/rewards/daily-login/claim",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200

        data = response.json()["data"]
        assert data["claimed"] is True
        assert data["reward_type"] == "daily_login"
        assert data["amount"] == 100
        assert "reward_id" in data
        assert "user_id" in data
        assert "reference_date" in data
        assert "created_at" in data

    async def test_claim_daily_login_second_time_returns_claimed_false(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """같은 날 두 번째 수령 시 claimed=False와 기존 정보를 반환합니다."""
        # Given: 사용자 생성 및 첫 번째 수령
        await client.post("/api/v1/users/me", headers=auth_headers)
        first_response = await client.post(
            "/api/v1/rewards/daily-login/claim",
            headers=auth_headers,
        )
        first_data = first_response.json()["data"]
        assert first_data["claimed"] is True

        # When: 두 번째 수령 시도
        second_response = await client.post(
            "/api/v1/rewards/daily-login/claim",
            headers=auth_headers,
        )

        # Then
        assert second_response.status_code == 200

        second_data = second_response.json()["data"]
        assert second_data["claimed"] is False
        assert second_data["reward_id"] == first_data["reward_id"]
        assert second_data["amount"] == 100

    async def test_claim_daily_login_without_user_returns_404(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자가 없으면 404 에러를 반환합니다."""
        # When: 사용자 생성 없이 보상 수령 시도
        response = await client.post(
            "/api/v1/rewards/daily-login/claim",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 404

    async def test_claim_daily_login_unauthorized(
        self,
        client: AsyncClient,
    ):
        """인증 없이 요청하면 403 에러를 반환합니다."""
        # When
        response = await client.post("/api/v1/rewards/daily-login/claim")

        # Then
        assert response.status_code == 403

    async def test_claim_daily_login_increases_user_points(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """보상 수령 시 사용자 포인트가 증가합니다."""
        # Given: 사용자 생성
        create_response = await client.post("/api/v1/users/me", headers=auth_headers)
        assert create_response.status_code == 201
        initial_points = create_response.json()["data"]["current_points"]

        # When: 일일 출석 보상 수령
        await client.post(
            "/api/v1/rewards/daily-login/claim",
            headers=auth_headers,
        )

        # Then: 사용자 포인트 확인
        me_response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert me_response.status_code == 200
        assert me_response.json()["data"]["current_points"] == initial_points + 100

    async def test_claim_daily_login_second_time_does_not_increase_points(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """두 번째 수령 시도 시 포인트가 증가하지 않습니다."""
        # Given: 사용자 생성 및 첫 번째 수령
        create_response = await client.post("/api/v1/users/me", headers=auth_headers)
        initial_points = create_response.json()["data"]["current_points"]

        await client.post(
            "/api/v1/rewards/daily-login/claim",
            headers=auth_headers,
        )

        # When: 두 번째 수령 시도
        await client.post(
            "/api/v1/rewards/daily-login/claim",
            headers=auth_headers,
        )

        # Then: 포인트는 한 번만 증가
        me_response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert me_response.json()["data"]["current_points"] == initial_points + 100

    async def test_claim_daily_login_idempotent(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """멱등성: 여러 번 호출해도 항상 200 OK를 반환합니다."""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When: 세 번 연속 호출
        responses = []
        for _ in range(3):
            response = await client.post(
                "/api/v1/rewards/daily-login/claim",
                headers=auth_headers,
            )
            responses.append(response)

        # Then: 모두 200 OK
        assert all(r.status_code == 200 for r in responses)

        # Then: 첫 번째만 claimed=True
        assert responses[0].json()["data"]["claimed"] is True
        assert responses[1].json()["data"]["claimed"] is False
        assert responses[2].json()["data"]["claimed"] is False


class TestDailyLoginRewardFlow:
    """일일 출석 보상 플로우 통합 테스트."""

    async def test_full_daily_login_reward_flow(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """전체 일일 출석 보상 플로우를 테스트합니다."""
        # 1. 사용자 생성 및 초기 포인트 확인
        create_response = await client.post("/api/v1/users/me", headers=auth_headers)
        assert create_response.status_code == 201
        initial_points = create_response.json()["data"]["current_points"]
        assert initial_points == 1000  # 가입 보너스

        # 2. 일일 출석 보상 수령
        claim_response = await client.post(
            "/api/v1/rewards/daily-login/claim",
            headers=auth_headers,
        )
        assert claim_response.status_code == 200
        assert claim_response.json()["data"]["claimed"] is True
        assert claim_response.json()["data"]["amount"] == 100

        # 3. 포인트 증가 확인
        me_response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert me_response.json()["data"]["current_points"] == 1100  # 1000 + 100

        # 4. 재수령 시도 (이미 받음)
        second_claim_response = await client.post(
            "/api/v1/rewards/daily-login/claim",
            headers=auth_headers,
        )
        assert second_claim_response.status_code == 200
        assert second_claim_response.json()["data"]["claimed"] is False

        # 5. 포인트 변화 없음 확인
        me_response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert me_response.json()["data"]["current_points"] == 1100

    async def test_multiple_users_reward_isolation(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
    ):
        """서로 다른 사용자의 보상은 격리됩니다."""
        # Given: 두 명의 사용자 생성
        headers_user1 = auth_headers_factory(
            provider_user_id="reward-user-1",
            email="reward1@example.com",
        )
        headers_user2 = auth_headers_factory(
            provider_user_id="reward-user-2",
            email="reward2@example.com",
        )

        await client.post("/api/v1/users/me", headers=headers_user1)
        await client.post("/api/v1/users/me", headers=headers_user2)

        # When: 각 사용자가 보상 수령
        response1 = await client.post(
            "/api/v1/rewards/daily-login/claim",
            headers=headers_user1,
        )
        response2 = await client.post(
            "/api/v1/rewards/daily-login/claim",
            headers=headers_user2,
        )

        # Then: 둘 다 claimed=True (서로 다른 사용자)
        assert response1.json()["data"]["claimed"] is True
        assert response2.json()["data"]["claimed"] is True

        # Then: 서로 다른 reward_id
        assert response1.json()["data"]["reward_id"] != response2.json()["data"]["reward_id"]
